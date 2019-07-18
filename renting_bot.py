#!/usr/bin/env python3
import tweepy
import logging
from config import create_api
import pandas as pd
import time
import re
import geopandas as gpd
from shapely.geometry import Point, Polygon
import shapely.wkt

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
        if(len(str(first_element_from_all_numbers)) >= 6):
            return first_element_from_all_numbers
        elif(len(str(first_element_from_all_numbers)) == 3):
            return first_element_from_all_numbers * 1000
        else:
            return first_element_from_all_numbers
    else:
        None

def get_renting_offers(user_price):
    df = pd.read_csv('https://raw.githubusercontent.com/crishernandezmaps/renting_bot/master/data/data.csv',sep=',')
    df['valorPesos'] = df['valorCLP']
    df['evaluation'] = df.apply(lambda row: checking_renting_prices(row,user_price), axis=1)
    dataframe_final = df.loc[(df['evaluation'] == 'Yes')]
    crs = {'init': 'epsg:4326'}
    # Points 
    geometry_for_points = [Point(xy) for xy in zip(dataframe_final['y'], dataframe_final['x'])]
    gdf_points = gpd.GeoDataFrame(dataframe_final, crs=crs, geometry=geometry_for_points)
    list_of_points = gdf_points.geometry.values

    # Polygons
    polygons = pd.read_csv('https://raw.githubusercontent.com/crishernandezmaps/renting_bot/master/data/comunas_RM.csv',sep=',')
    geometry_for_polygons = polygons['WKT'].map(shapely.wkt.loads)
    polygons = polygons.drop('WKT', axis=1)
    gdf_polygons = gpd.GeoDataFrame(polygons, crs=crs, geometry=geometry_for_polygons)
    list_of_polygons = gdf_polygons.geometry.values   

    def check_points_against_polygons(x):
        r = []
        for i in list_of_points:
            if(i.within(x)):
                r.append(i)
            else:
                pass
        return len(r) 

    gdf_polygons['freq'] = gdf_polygons['geometry'].map(check_points_against_polygons)
    first_five_comunas = gdf_polygons.sort_values(['freq'],ascending=False).head(5)
    first_five_comunas['total'] = first_five_comunas['NOM_COMUNA'] + ': ' + first_five_comunas['freq'].astype('str')
    resultant_object = {
        "first_place":first_five_comunas.total.values[0],
        "second_place":first_five_comunas.total.values[1],
        "third_place":first_five_comunas.total.values[2],
        "fourth_place":first_five_comunas.total.values[3],    
        "fifth_place":first_five_comunas.total.values[4]   
    }    

    resulting_info = {
        "total_offer": "Total Ofertas: {}".format(len(df.valorCLP.values)),
        "your_offer": "Ofertas para tu capacidad de arriendo: {}".format(len(dataframe_final.valorCLP.values)),
        "your_percentage": "(%)Ofertas para tu capacidad de arriendo: {}%".format(round(100*(len(dataframe_final.valorCLP.values)/len(df.valorCLP.values)),0)),
        "one":resultant_object["first_place"],
        "two":resultant_object["second_place"],        
        "three":resultant_object["third_place"],
        "four":resultant_object["fourth_place"],
        "five":resultant_object["fifth_place"]        
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
                to_tweet = f"@{returned_name} El Total de arriendos esta semana es de {final_info_user['total_offer'].split(':')[-1].strip()}. Con ese monto de arriendo ({ammount_from_user}) accedes a {final_info_user['your_offer'].split(':')[-1].strip()} deptos ({final_info_user['your_percentage'].split(':')[-1].strip()}). Ranking de ofertas por comuna(top5): {final_info_user['one']}, {final_info_user['two']}, {final_info_user['three']}, {final_info_user['four']}, {final_info_user['five']}"
                logger.info(to_tweet)

                if(len(to_tweet)<=280):
                    api.update_status(
                        status=to_tweet,
                        in_reply_to_status_id=tweet.id
                    )
                    print('success!')
                else:
                    pass
            else:
                api.update_status(
                    status="Por favor dame un número para poder evaluar. El tweet debe ser de la siguiente forma: @Welokat #dondeArremdar 500000 (o el número que desees. Sin puntos)",
                    in_reply_to_status_id=tweet.id
                )


    return new_since_id

def main():
    api = create_api()
    since_id = 1
    while True:
        since_id = check_mentions(api, ['dondeArrendar'], since_id)
        time.sleep(45)

if __name__ == "__main__":
    main()   