from telegram_notifier import send_message

import json 
import requests
import asyncio
import time
import toml

config = toml.load('config.toml')
telegram_ids = config['telegram']['ids']
telegram_admin_ids = config['telegram']['admin_ids']

date = config['query_settings']['date']
hut_id = config['query_settings']['hut_id']

room_types = {'7': 'Matratzenlager', '8': 'Mehrbettzimmer', '9': 'Zweierzimmer'}


hut_link = f'https://www.alpsonline.org/reservation/calendar?hut_id={hut_id}&header=no'
query_link = f'https://www.alpsonline.org/reservation/selectDate?date={date}'

counter = 0
error_counter = 0

for telegram_id in telegram_admin_ids:
    asyncio.run(send_message("The fetcher has been started!", telegram_id))

while True:
    try:
        while True:
            session = requests.Session()
            session.get(hut_link)

            request_cookies = session.cookies.get_dict()
            headers = {'User-Agent': 'Mozilla/5.0'}

            raw_reservations = requests.get(query_link, cookies=request_cookies, headers=headers).text
            parsed_reservations = json.loads(raw_reservations)

            reservations_on_selected_date = parsed_reservations['0']

            total_number_of_free_rooms = 0
            message = ''
            for room_type in reservations_on_selected_date:
                room_type_name = room_types[str(room_type['bedCategoryId'])]
                free_rooms = room_type['freeRoom']
                total_number_of_free_rooms += free_rooms
                total_rooms = room_type['totalRoom']
                reserved_rooms_ratio = room_type['reservedRoomsRatio']
                message += f'{room_type_name} ({free_rooms}/{total_rooms}) - {reserved_rooms_ratio * 100:.2f}% reserved\n'

            if total_number_of_free_rooms > 0:
                message += f"\nThere are {total_number_of_free_rooms} free rooms available at the hut on {date}!\n\n"
                for telegram_id in telegram_ids:
                    asyncio.run(send_message(message, telegram_id))

            print(message)

            if counter >= 30:
                for telegram_id in telegram_admin_ids:
                    asyncio.run(send_message(message, telegram_id))

                counter = 0

            time.sleep(60)
            counter += 1

    except Exception as e:
        print(e)
        
        error_counter += 1 
        if error_counter <=10:
            for telegram_id in telegram_admin_ids:
                asyncio.run(send_message(f"An error occurred: {e}\nExecution resumes in 120 seconds!", telegram_id))
            
            time.sleep(120)

        else:  
            for telegram_id in telegram_admin_ids:
                asyncio.run(send_message(f"An error occurred: {e}\nExecution halted!", telegram_id))
            raise e
