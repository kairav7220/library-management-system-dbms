from dotenv import load_dotenv
from datetime import datetime
from mysql_client import get_worksheet

load_dotenv()

worksheet = get_worksheet('Logs')
users_table = get_worksheet('User Table')

def login(username, password):
    all_values = users_table.get_all_values()
    for i in all_values[1:]:
        if username == i[3] and password == i[4]:
            print('Successful Login!')
            values = [
                '=ROW()',
                datetime.now().strftime('%d-%m-%Y %I:%M:%S %p'),
                f'{username} has logged in'
            ]
            worksheet.append_row(values, value_input_option='USER_ENTERED')

print(login('user1', 'user123'))

def logout(username):
    values = [
        '=ROW()',
        datetime.now().strftime('%d-%m-%Y %I:%M:%S %p'),
        f'{username} has logged out'
    ]
            
    worksheet.append_row(values, value_input_option='USER_ENTERED')

print(logout('user1'))