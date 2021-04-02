# Write your code here
import math
from random import randint
import sqlite3
from sqlite3 import Error
import os.path

def create_connection(db_file):
    file_exists = os.path.isfile(db_file)
    if not file_exists:
        open(db_file, 'w+')

    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    return conn


conn = create_connection(r"card.s3db")
cur = conn.cursor()
cur.execute('''create table if not exists card
             (id INTEGER, number TEXT , pin TEXT , balance INTEGER DEFAULT 0)''')
conn.commit()

user_input = ''
is_logged_in = False
logged_card_number = ''
logged_card_pin = ''


def random_with_N_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return randint(range_start, range_end)


def process_odd_number(num):
    res = num * 2
    if res > 9:
        res = res - 9
    return res


def round_up(n, decimals=0):
    multiplier = 10 ** decimals
    return int(math.ceil(n * multiplier) / multiplier)


def generate_checksum(acc_id):
    processed_numbers = []
    arr = list(acc_id)
    for n, val in enumerate(arr):
        if ((n + 1) % 2 != 0):
            processed_number = process_odd_number(int(val))
            processed_numbers.append(processed_number)
        else:
            processed_numbers.append(int(val))

    sum = 0
    for n in processed_numbers:
        sum = sum + n
    return str(round_up(sum, -1) - sum)


def create_bank_card_id(length=16):
    bin = random_with_N_digits(9)
    if 16 < length < 20:
        bin = random_with_N_digits(length - 7)
    acc_id = '400000{bin}'.format(bin=bin)
    checksum = generate_checksum(acc_id)
    return acc_id + checksum


def check_card_id(card_id):
    if not is_valid_by_luhns_algorithm(card_id):
        return 'Probably you made mistake in the card number. Please try again!'
    if not is_card_exist_in_db(card_id):
        return 'Such a card does not exist.'
    return None


def is_valid_by_luhns_algorithm(card_id):
    card_checksum = int(card_id[len(card_id)-1])
    required_checksum = generate_checksum(card_id[:-1])
    return int(required_checksum) == card_checksum


def is_card_exist_in_db(card_id):
    if card_id is not None and 15 < len(card_id) < 20:
        sql_query = '''
            SELECT * from card WHERE number={number};
            '''.format(number=card_id)
        cur.execute(sql_query)
        data = cur.fetchall()
        return len(data) > 0
    return None


class BankCard:
    def __init__(self):
        self.id = create_bank_card_id()
        self.pin = str(random_with_N_digits(4))


def create_card():
    user_card = BankCard()
    sql_query = '''
    INSERT INTO card (number, pin) VALUES({number}, {pin});
    '''.format(number=user_card.id, pin=user_card.pin)
    cur.execute(sql_query)
    conn.commit()
    print('Your card has been created')
    print('Your card number:')
    print(user_card.id)
    print('Your card PIN:')
    print(user_card.pin)


def add_income(user_card_id, user_card_pin, amount):
    sql_query = '''
    UPDATE card SET balance = balance + {amount} WHERE number={number} AND pin={pin}
    '''.format(number=user_card_id, pin=user_card_pin, amount=amount)
    cur.execute(sql_query)
    conn.commit()
    print('Income was added!')


def make_transfer(to_card_number, transfer_amount_input):
    is_balance_bigger_than_transfer = is_balance_allows_transfer(transfer_amount_input)
    if is_balance_bigger_than_transfer:
        sql_query_to_pull_money = '''
        UPDATE card SET balance = balance - {amount} WHERE number={number}
            '''.format(number=logged_card_number, amount=transfer_amount_input)
        cur.execute(sql_query_to_pull_money)

        sql_query_to_put_money = '''
        UPDATE card SET balance = balance + {amount} WHERE number={number}
                '''.format(number=to_card_number, amount=transfer_amount_input)
        cur.execute(sql_query_to_put_money)
        conn.commit()
        print('Success!')
    else:
        print('Not enough money!')


def get_card_data_from_db(user_card_id, user_card_pin):
    if user_card_id is not None and 15 < len(user_card_id) < 20 and user_card_pin is not None and len(user_card_pin) == 4:
        sql_query = '''
            SELECT number, pin, balance from card WHERE number={number} AND pin={pin};
            '''.format(number=user_card_id, pin=user_card_pin)
        cur.execute(sql_query)
        return cur.fetchone()
    return None


def close_account():
    sql_query = '''
                DELETE from card WHERE number={number};
                '''.format(number=logged_card_number)
    cur.execute(sql_query)
    conn.commit()
    global is_logged_in
    is_logged_in = False
    print('The account has been closed!')


def is_balance_allows_transfer(transfer_amount_input):
    card_data = get_card_data_from_db(logged_card_number, logged_card_pin)
    card_number, pin, balance = card_data
    return balance > transfer_amount_input


def handle_login():
    user_card_id = str(input('Enter your card number: '))
    user_card_pin = str(input('Enter your PIN: '))
    card_data = get_card_data_from_db(user_card_id, user_card_pin)
    if card_data is not None:
        card_number, pin, balance = card_data
        if card_number is not None and pin == user_card_pin:
            global is_logged_in
            global logged_card_number
            global logged_card_pin
            is_logged_in = True
            logged_card_number = card_number
            logged_card_pin = pin
            print('You have successfully logged in!')
            return
    print('Wrong card number or PIN!')


def show_user_interface():
    global user_input
    user_input = str(
        input(' 1. Create an account \n 2. Log into account \n 0. Exit \n'))
    if user_input == '1':
        create_card()
    elif user_input == '2':
        handle_login()


def show_logged_user_interface():
    global user_input
    user_input = str(
        input(' 1. Balance \n 2. Add income \n 3. Do transfer \n 4. Close account \n 5. Log out \n 0. Exit \n'))
    if user_input == '1':
        card_data = get_card_data_from_db(logged_card_number, logged_card_pin)
        card_number, pin, balance = card_data
        print('Balance: {}'.format(balance))
    elif user_input == '2':
        income_amount_input = int(input('Enter income:'))
        add_income(logged_card_number, logged_card_pin, income_amount_input)
    elif user_input == '3':
        print('Transfer')
        recepient_card_id_input = str(input('Enter card number:'))
        card_errors = check_card_id(recepient_card_id_input)
        if card_errors is None:
            transfer_amount_input = int(input('Enter how much money you want to transfer:'))
            make_transfer(recepient_card_id_input, transfer_amount_input)
        else:
            print(card_errors)
    elif user_input == '4':
        close_account()
    elif user_input == '5':
        global is_logged_in
        is_logged_in = False
        print('You have successfully logged out!')


while user_input != '0':
    if is_logged_in:
        show_logged_user_interface()
    else:
        show_user_interface()

    if user_input == '0':
        print('Bye!')
        break
