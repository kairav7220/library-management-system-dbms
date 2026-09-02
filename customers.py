from dotenv import load_dotenv
import random
from mysql_client import get_worksheet

load_dotenv()

worksheet = get_worksheet('Customer Table')

def add_customer():
    try:
        CustID = input('Enter Customer ID: ')
        Name = input('Enter Name: ')
        Username = input('Enter Username: ')
        Password = input('Enter Password: ')
        worksheet.append_row([CustID, Name, Username, Password])
        print('Customer added successfully!')
    except Exception as e:
        print(f'Error adding customer: {e}')

add_customer()