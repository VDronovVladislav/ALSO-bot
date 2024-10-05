"""Код импорта данных из xlsx в объект DataFrame а затем в словарь python."""
import pandas as pd


excel_data = pd.read_excel('data.xlsx')
data = pd.DataFrame(
    excel_data,
    columns=['chat_id', 'chat_name', 'button_url', 'additional_text']
)

DATA_DICT = dict(zip(data.chat_id, data.additional_text))
