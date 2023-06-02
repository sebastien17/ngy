# -*- coding: utf-8 -*-
import ngy
import datetime

def __execute_locus():
    import fire
    fire.Fire(__locus_fetch_save)

def __locus_fetch_save(lat1: float, long1: float, lat2: float, long2: float, position_name: str) -> None:
    my_request = ngy.Request(( lat1, long1, lat2, long2),
                         zoom_list=range(6,16),
                         layer="GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN25TOUR.CV",
                         style="normal",
                         projection="PM",
                         format="jpeg")
    print('Fetching data : ')
    my_request.fetch_data()

    _now = datetime.datetime.now()
    my_request.save(position_name +'.mbtiles', position_name.capitalize() + ' - ' + _now.strftime("%d/%m/%Y"))
    print('Data saved to : ' + position_name +'.mbtiles')
    
    