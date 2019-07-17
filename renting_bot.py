#!/usr/bin/env python3
import tweepy
import logging
from config import create_api
import pandas as pd
import time
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def checking_renting_prices(row,up):
    try:
        value_converted_to_int = int(row['valorCLP'])
        if(value_converted_to_int <= up):
            return 'Yes'
        else:
            return 'No'
    except:
        pass

def get_number_in_tweet(incoming_tweet_text): 
    get_all_numbers = re.findall(r'[0-9]+', incoming_tweet_text)
    if(len(get_all_numbers)>0):
        first_element_from_all_numbers = int(get_all_numbers[0])
        return first_element_from_all_numbers
    else:
        None

def get_renting_offers(user_price):
    df = pd.read_csv('https://raw.githubusercontent.com/crishernandezmaps/renting_bot/master/data.csv',sep=',')
    df['valorPesos'] = df['valorCLP']
    df['evaluation'] = df.apply(lambda row: checking_renting_prices(row,user_price), axis=1)
    dataframe_final = df.loc[(df['evaluation'] == 'Yes')]
    dataframe_final.to_csv('toMap.csv',sep=',')

    resulting_info = {
        'total_offer': 'Total Ofertas: {}'.format(len(df.valorCLP.values)),
        'your_offer': 'Ofertas para tu capacidad de arriendo: {}'.format(len(dataframe_final.valorCLP.values)),
        'your_percentage': '(%)Ofertas para tu capacidad de arriendo: {}%'.format(round(100*(len(dataframe_final.valorCLP.values)/len(df.valorCLP.values)),3))
    } 
    return resulting_info


def check_mentions(api, keywords, since_id):
    logger.info("Retrieving mentions")
    new_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline,since_id=since_id).items():
        new_since_id = max(tweet.id, new_since_id)
        if tweet.in_reply_to_status_id is not None:
            continue
        if any(keyword in tweet.text.lower() for keyword in keywords):
            returned_name = tweet.user.screen_name
            returned_text = tweet.text
            ammount_from_user = get_number_in_tweet(returned_text)
            if(ammount_from_user):
                final_info_user = get_renting_offers(ammount_from_user)
                to_tweet = f"Hola @{returned_name}! El total de ofertas de arriendo en Santiago esta semana es de <{final_info_user['total_offer'].split(':')[-1].strip()}>. Lo que destinarias para arriendo ({ammount_from_user}) te permite acceder a <{final_info_user['your_offer'].split(':')[-1].strip()}> departamentos, lo que representa un <{final_info_user['your_percentage'].split(':')[-1].strip()}> del total de ofertas para esta semana. Saludos!"
                logger.info(to_tweet)

                # api.update_status
                api.update_with_media(
                    'img/tree.jpg',
                    status=to_tweet,
                    in_reply_to_status_id=tweet.id
                )
            else:
                api.update_with_media(
                    'img/tree.jpg',
                    status="Por favor dame un número para poder evaluar. El tweet debe ser de la siguiente forma: @crishernandezco #dondepuedoarrendar 500000 (o el número que desees. Sin punto)",
                    in_reply_to_status_id=tweet.id
                )


    return new_since_id

def main():
    api = create_api()
    since_id = 1
    while True:
        since_id = check_mentions(api, ['dondepuedoarrendar'], since_id)
        time.sleep(45)

if __name__ == "__main__":
    main()

# Todo bien excepto que ahora me arroja 0 en las ofertas. 
# Arreglar esto mas agregar una imagen, mas cambiarlo de cuenta y todo listo.    