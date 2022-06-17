import tabula
import pandas as pd


def pdf_edit(file_path):
    
    pdf_data = tabula.read_pdf(file_path, lattice=True, pages='1')
    df = pd.DataFrame()
    for i in pdf_data:
        df = pd.concat([df, i])
        
    col_name = df.columns
    for i in col_name[1:]:
        df[i] = df[i].str.replace(',', '').astype(int)
        
    col_rename = {
        '月次': 'YYYY-MM',
        '運航回数【回】': 'Flights',
        '旅客数【人】': 'PAX',
        '座席数【席】': 'Seats',
        '貨物重量【Kg】': 'Cargo(kg)',
        '郵便物重量【Kg】': 'Mail(kg)'
        }
    df.rename(columns=col_rename, inplace=True)
    
    df['Payload(kg)'] = (df['PAX'] * 65) + df['Cargo(kg)'] + df['Mail(kg)']
    df['LoadFactor(%)'] = (df['PAX'] / df['Seats']).map('{:.1%}'.format)
    
    file_path = file_path.replace('.pdf', '.xlsx')
    file_path = file_path.replace('static', 'download')
    
    df.to_excel(file_path, index=False) 


if __name__ == '__main__':
    file_path = 'static/sample1.pdf'
    pdf_edit(file_path)
    
    