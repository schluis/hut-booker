import asyncio
import json
import time
from datetime import datetime, timedelta

import requests
import toml

from telegram_notifier import send_message

config = toml.load("config.toml")
telegram_ids = config["telegram"]["ids"]
telegram_admin_ids = config["telegram"]["admin_ids"]

date = config["query_settings"]["date"]
days = config["query_settings"]["days"]
hut_id = config["query_settings"]["hut_id"]
query_interval = config["query_settings"]["interval"]

room_types = {"7": "Matratzenlager", "8": "Mehrbettzimmer", "9": "Zweierzimmer"}


hut_link = f"https://www.alpsonline.org/reservation/calendar?hut_id={hut_id}&header=no"
query_link = f"https://www.alpsonline.org/reservation/selectDate?date={date}"

error_counter = 0
last_sent_message = ""
hard_error_message = ""

for telegram_id in telegram_admin_ids:
    asyncio.run(send_message("Service up and running...", telegram_id))

while True:
    try:
        while True:
            try:
                while True:
                    session = requests.Session()
                    session.get(hut_link)

                    request_cookies = session.cookies.get_dict()
                    headers = {"User-Agent": "Mozilla/5.0"}

                    raw_reservations = requests.get(
                        query_link, cookies=request_cookies, headers=headers
                    ).text
                    parsed_reservations = json.loads(raw_reservations)

                    message = ""
                    for day in range(days):
                        reservations_on_selected_date = parsed_reservations[str(day)]

                        total_number_of_free_rooms = 0
                        selected_date = datetime.strptime(date, "%d.%m.%Y") + timedelta(
                            days=day
                        )
                        message += f"Reservations for {selected_date.date().strftime('%d.%m.%Y')}:\n"

                        for room_type in reservations_on_selected_date:
                            room_type_name = room_types[str(room_type["bedCategoryId"])]
                            free_rooms = room_type["freeRoom"]
                            total_number_of_free_rooms += free_rooms
                            total_rooms = room_type["totalRoom"]
                            reserved_rooms_ratio = room_type["reservedRoomsRatio"]
                            message += f"{room_type_name} ({free_rooms}/{total_rooms}) - {reserved_rooms_ratio * 100:.2f}% reserved\n"

                        if total_number_of_free_rooms > 0:
                            message += f"\nThere are {total_number_of_free_rooms} free rooms available at the hut!\n"

                        message += "\n"

                    if message != last_sent_message:
                        print(message)
                        for telegram_id in telegram_ids:
                            asyncio.run(send_message(message, telegram_id))

                        last_sent_message = message

                    if datetime.now().hour == 7 and datetime.now().minute == 0:
                        error_counter = 0
                        for telegram_id in telegram_admin_ids:
                            asyncio.run(
                                send_message(
                                    "Service still up and running...", telegram_id
                                )
                            )

                    if hard_error_message != "":
                        for telegram_id in telegram_admin_ids:
                            asyncio.run(send_message(hard_error_message, telegram_id))
                        hard_error_message = ""

                    time.sleep(query_interval)

            except Exception as e:
                print(e)

                error_counter += 1
                if error_counter <= 20:
                    for telegram_id in telegram_admin_ids:
                        asyncio.run(
                            send_message(
                                f"An error occurred: {e}\nExecution resumes in 120 seconds!",
                                telegram_id,
                            )
                        )

                    time.sleep(120)

                else:
                    for telegram_id in telegram_admin_ids:
                        asyncio.run(
                            send_message(
                                f"An error occurred: {e}\nExecution halted!",
                                telegram_id,
                            )
                        )
                    print(e)
                    print("Aborting execution")
                    exit()

    except Exception as e:
        print(e)
        hard_error_message += f"Hard error occurred: {e}\n"
        error_counter += 1

        if error_counter <= 20:
            print("Aborting execution")
            exit()

        time.sleep(600)
