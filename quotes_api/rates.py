#!/usr/bin/env python
# coding: utf-8


import asyncio
import aiohttp
import json
import redis
import pandas as pd
from tabulate import tabulate
from enum import Enum
from django.conf import settings
from .currencies import supported_currencies


# Useful for debugging
RETURN_EXCEPTIONS = True


# The implementation is dependant on these URLs so it will need to change if these values change:
OPEN_RATES_URL = 'http://api.openrates.io/latest'
EXCHANGE_RATE_URL = 'https://api.exchangerate-api.com/v4/latest/'


def get_other_supported_currencies(base_currency):
    """Get all supported currencies except this base currency.
    Example:
    get_other_supported_currencies("USD")=>
    (EUR,ILS)
    """
    return tuple([currency for currency in supported_currencies if currency != base_currency])


def get_openrates_params(base): #base -> base currency
    """Generates the parms for an openrates api request
    Example:
    get_params("USD")=>
    {'base': 'USD', 'symbols': 'EUR,ILS'}
    """
    symbols = ','.join(get_other_supported_currencies(base))
    return locals()


async def response_to_rates_json(response, base_currency):
    """Extracts supported currencies and filtes out unneeded fields."""
    text = await response.text()
    rates = json.loads(text)['rates']
    supported_currencies = get_other_supported_currencies(base_currency)
    results = {a_key:rates[a_key] for a_key in rates.keys()
               if a_key in supported_currencies}
    return results    


def check_for_missing_or_invalid_rates(source, rates, base_currency):
    for currency in get_other_supported_currencies(base_currency):
        problem = check_amount(rates[currency])
        if problem is not None:
            del rates[currency] # log problem


async def get_rates_from_openrates(session, base_currency):
    """Example:
    await get_rates_from_openrates(session, "USD")=>
    {'EUR': 0.8389261745, 'ILS': 3.3077181208}
    """
    response = await session.get(OPEN_RATES_URL,
                                 params=get_openrates_params(base_currency))
    rates = await response_to_rates_json(response, base_currency)
    check_for_missing_or_invalid_rates(OPEN_RATES_URL, rates, base_currency)
    return rates


async def get_rates_from_exchange_rate(session, base_currency):
    """Example:
    await get_rates_from_exchange_rate(session, "USD")=?
    {'EUR': 0.837996, 'ILS': 3.323482}
    """
    response = await session.get(EXCHANGE_RATE_URL+base_currency)
    rates = await response_to_rates_json(response, base_currency)
    check_for_missing_or_invalid_rates(OPEN_RATES_URL, rates, base_currency)
    return rates


async def get_rates(base_currency):
# Get both rates in one sessionasync def get_rates(base_currency):
    """Gets rates from both APIs.
    Example:
    await get_rates("USD")=>
    [{'EUR': 0.8389261745, 'ILS': 3.3077181208},
     {'EUR': 0.837996, 'ILS': 3.323482}]
    """
    sources = (get_rates_from_openrates,
               get_rates_from_exchange_rate)
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(
                 a_source(session, base_currency))
                 for a_source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results


async def get_max_rates(base_currency):
    """Gets the highest rates from third party sources (not from cache)."""
    rates_list = await get_rates(base_currency)
    df = pd.DataFrame(rates_list, ('openrates', 'exchange_rates'))
    print(tabulate(df, headers='keys', tablefmt='psql'))
    return dict(df.max(axis=0))


def get_ratio(base_currency, to_currency):
    """Adds a colon between the currency types
    Example:
    get_ratio("USD", "ILS")=>
    "USD:ILS"
    """
    return base_currency+":"+to_currency


async def refresh_rates_cache(base_currency, cache):
    """Updates the Redis cache with recent values."""
    rates = await get_max_rates(base_currency)
    for to_currency, a_rate in rates.items():
        cache.set(get_ratio(base_currency, to_currency), a_rate, settings.CACHE_LIFE_TIME)


async def get_a_rate(from_currency_code, to_currency_code, cache):
    """Gets a rate from the cache when possible.
    Otherwise updates the cache with fresh values.
    """
    ratio = get_ratio(from_currency_code, to_currency_code)
    if not cache.exists(ratio):
        await refresh_rates_cache(from_currency_code, cache)
    return cache.get(ratio)


def create_response(exchange_rate, currency_code, amount):
    print(f'response:\n{locals()}')
    return json.dumps(locals())


def is_currency_supported(currency, problem_type):
    if currency not in supported_currencies:
        return problem_type.value.format(currency=currency)


class Problem(Enum):
    MISSING_CURRENCY = "The exchange rate for {currency} is missing."
    SERVICE_DOWN = "The service is temporarily down for maintenance."
    NOT_A_NUMBER = "The specified 'amount'={amount} is not a number. Please specify a positive numeric value."
    NOT_POSITIVE = "The specified 'amount'={amount} is not a positive number."
    FROM_CURRENCY = "The 'from_currency_code'={currency} is not supported." 
    TO_CURRENCY = "The 'to_currency_code'={currency} is not supported."


# Checks

def check_amount(amount):
    try:
        amount = float(amount)
    except:
        return Problem.NOT_A_NUMBER.value.format(amount=amount)
    else:
        if amount <= 0:
            return Problem.NOT_POSITIVE.value.format(amount=amount)


def check_key_count(rates, source):
    expected_key_count = len(supported_currencies)-1
    actual_valid_key_count = len(rates)
    if actual_valid_key_count != expected_key_count:
        pass #MONGOLOG


def check_rates_response(rates, source):
    if check_key_count(rates):
        for a_key in valid_keys:
            problem = check_amount(rates[a_key])
            if problem:
                pass #MONOGOLOG
    else:
        pass #MONGOLOG missing key(s)
    

def check_params(from_currency_code, amount, to_currency_code, **kwargs):
    problems = []
    problems.append(check_amount(amount))
    problems.append(is_currency_supported(from_currency_code, Problem.FROM_CURRENCY))
    problems.append(is_currency_supported(to_currency_code, Problem.TO_CURRENCY))
    problems = [a_problem for a_problem in problems if a_problem]
    return problems


async def get_quote(from_currency_code, amount, to_currency_code):
    """Getting a quote will refresh outdated cache records."""
    print(f'request:\n{locals()}')
    cache = redis.StrictRedis(settings.REDIS_HOST, settings.REDIS_PORT)
    problems = check_params(**locals())
    if not problems:
        rate = await get_a_rate(from_currency_code, to_currency_code, cache)
        problem = check_amount(rate)
        if problem:
            return {"Error": Problem.SERVICE_DOWN.value}
        else:
            return create_response(f'{float(rate):.3f}', to_currency_code, f'{float(amount)*float(rate):.5f}')
    else:
        return {"Error": problems}
