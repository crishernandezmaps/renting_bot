#!/usr/bin/env python3
import tweepy
import logging
from config import create_api
import time
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def check_mentions(api, keywords, since_id):
    logger.info("Retrieving mentions")
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline,since_id=since_id).items():
        new_since_id = max(tweet.id, new_since_id)
        if tweet.in_reply_to_status_id is not None:
            continue
        if any(keyword in tweet.text.lower() for keyword in keywords):
            returned_id = tweet.user.id
            returned_name = tweet.user.name
            returned_text = tweet.text
            returned_location = None
            returned_place = None
            if(tweet.user.location):
                returned_location = tweet.user.location
            if(tweet.place):
                returned_place = tweet.place

            final_result = {
                'id': returned_id,
                'name': returned_name,
                'text': returned_text.strip(),
                'location': returned_location,
                'place': returned_place
            }

            logger.info(f"User: {final_result}")
            print(final_result)

            api.update_status(
                status="Please reach us via DM",
                in_reply_to_status_id=tweet.id,
            )

    return new_since_id

def main():
    api = create_api()
    since_id = 1
    while True:
        # print(since_id)
        since_id = check_mentions(api, ['wheretolive'], since_id)
        time.sleep(60)

if __name__ == "__main__":
    main()


'''
Objetivo: valor del arriendo por comuna y su relación con el sueldo miínimo u otra medida de comparación
- Use Scrapy instead of Bs4
- Cantidad de Proyectos
- Valor del arriendo en pesos
- Localización de la propiedad mas barata
- Mapa coroplético resultante
'''
