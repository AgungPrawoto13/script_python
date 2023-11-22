# STRING MATCHING LONG LAT
import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely.geometry import Point


# Baca file JSON polygon spatial
spatial_data = st.sidebar.file_uploader("Upload an Excel file", type=["json"], accept_multiple_files=False)
# Baca file raw data
data = st.sidebar.file_uploader("Upload an Excel file", type=["xlsx", "xls"], accept_multiple_files=False)
index = input("Masukan index")
# Ganti 1190 menjadi urutan selanjutnya di file gerak kinetik 
data.insert(0, 'index', range(index, index + len(data)))
# Hilangkan tanda kurung siku "[" dan "]" dari kolom "lokasi_koordinat"
data['lokasi_koordinat'] = data['lokasi_koordinat'].str.replace('[', '').str.replace(']', '')

# Pemecahan kolom 'Kota' menjadi dua kolom 'Kota1' dan 'Kota2' dengan delimiter koma
data[['long', 'lat']] = data['lokasi_koordinat'].str.split(',', expand=True)

# Hapus kolom "lokasi_koordinat" jika tidak diperlukan lagi
data = data.drop('lokasi_koordinat', axis=1)

data['long']= data['long'].astype(float)
data['geometry'] = data.apply(lambda row: Point(row['long'], row['lat']), axis=1)

# Menambahkan 5 kolom baru dengan nilai awal kosong (NaN)
# data['Kelurahan'] = None
data['Kecamatan'] = None
data['Kabupaten'] = None
data['Provinsi'] = None
data['Kode_Prov_Kemendagri']=None
data['Kode_Kab_Kemendagri']=None
data['Kode_Kec_Kemendagri']=None
# data['Kode_Kel_Kemendagri']=None

for index, row in data.iterrows():
    point = row['geometry']
    matching_polygon = spatial_data[spatial_data.contains(point)]
    
    if not matching_polygon.empty:
        # data.loc[index,"Kelurahan"] = matching_polygon['WADMKD'].values[0]
        data.loc[index,"Kecamatan"] = matching_polygon['nama_kec'].values[0]
        data.loc[index,"Kabupaten"] = matching_polygon['nama_kab'].values[0]
        data.loc[index,"Provinsi"] = matching_polygon['nama_pro'].values[0]
        data.loc[index,"Kode_Prov_Kemendagri"] = matching_polygon['kode_pro_kemendagri'].values[0]
        data.loc[index,"Kode_Kab_Kemendagri"] = matching_polygon['kode_kab_kemendagri'].values[0]
        data.loc[index,"Kode_Kec_Kemendagri"] = matching_polygon['kode_kec_kemendagri'].values[0]
        # data.loc[index,"Kode_Kel_Kemendagri"] = matching_polygon['KDEPUM'].values[0]

# PARSING DATA
import ast
pd.set_option('display.max_column', None)

def safe_eval(s):
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return {}
    
# EFEK THD KANDIDAT
data['kolom1'] = data['efek_terhadap_kandidat'].apply(safe_eval)

# Mengambil semua keys dari dictionary dalam kolom1
keys = data['kolom1'].apply(lambda x: list(x.keys())).explode().unique()

# Mengisi kolom-kolom baru dengan nilai-nilai yang sesuai
for key in keys:
    data[key] = data['kolom1'].apply(lambda x: x.get(key, None))

# KONSTITUENSI
data['kolom2'] = data['konstituensi'].apply(safe_eval)

# Mengambil semua keys dari dictionary dalam kolom1
keys = data['kolom2'].apply(lambda x: list(x.keys())).explode().unique()

# Mengisi kolom-kolom baru dengan nilai-nilai yang sesuai
for key in keys:
    data[key] = data['kolom2'].apply(lambda x: x.get(key, None))

# mengambil kolom sesuai dengan kolom di Tableau
data_gerak = data[['index', 'Kode_Kab_Kemendagri', 'Kode_Kec_Kemendagri', 'waktu_sebelum', 'waktu_sesudah',
       'entitas_tipe', 'entitas_nama','entitas_arah_dukungan', 'entitas_spektrum', 'entitas_tokoh_internal',
       'entitas_keterangan', 'agenda_aktivitas', 'agenda_substansi', 'agenda_konklusi_gerak',
       'lokasi_negara', 'lokasi_spesifik', 'Provinsi', 'Kabupaten',
       'Kecamatan', 'long', 'lat', 'dimensi_aktor', 'dimensi_organisasi',
       'konstituensi', 'efek_terhadap_kandidat', 'cakupan_efek', 'saran',
       'alert']]

# Save data
# data.to_excel("C:/Dattabot/Dashboard Agenda Kinetik/data_raw_parsing.xlsx", index=False,engine='openpyxl')
data_gerak.to_excel("../gerak kinetik/result_script/Gerak Kinetik Capres-Cawapres.xlsx", index=False)

# copy data
data1 = data.copy()

# GANJAR PRANOWO
# Melakukan one-hot encoding menggunakan pd.get_dummies
one_hot_encoded1 = pd.get_dummies(data1, columns=['ganjar_pranowo'], dtype='int')
# Mengambil kolom yang diperlukan
data_gp = one_hot_encoded1[['index'] + list(one_hot_encoded1.columns[-3:])]
# Buat DataFrame dengan beberapa kolom
data = {
    'index':[],
    'ganjar_pranowo_Negatif': [],
    'ganjar_pranowo_Neutral': [],
    'ganjar_pranowo_Positif': []
}
df_etk = pd.DataFrame(data)
# Melakukan concat
datagp = pd.concat([df_etk,data_gp],ignore_index=True)
# Melakukan rename koom 
datagp.rename(columns={'ganjar_pranowo_Negatif': 'Negatif', 'ganjar_pranowo_Neutral': 'Neutral','ganjar_pranowo_Positif':'Positif'}, inplace=True)
# Melakukan unpivot
unp_gp = pd.melt(datagp, id_vars=['index'], var_name='ganjar_pranowo', value_name='Value')

# Menghapus baris dengan nilai selain "Positif", "Negatif", dan "Netral" di kolom "Sentimen"
allowed_values = ['Positif', 'Negatif', 'Neutral']
unp_gp = unp_gp.loc[unp_gp['ganjar_pranowo'].isin(allowed_values)]

unp_gp=unp_gp.dropna()
# Mengubah tipe data
unp_gp['index']=unp_gp['index'].astype(int)
unp_gp['Value']=unp_gp['Value'].astype(int)

# save data
unp_gp.to_excel("../gerak kinetik/result_script/Sentimen_GP.xlsx",index=False)

# PRABOWO SUBIANTO
one_hot_encoded2 = pd.get_dummies(data1, columns=['prabowo_subianto'], dtype='int')
# Mengambil kolom yang diperlukan
data_ps = one_hot_encoded2[['index'] + list(one_hot_encoded2.columns[-3:])]

# Buat DataFrame dengan beberapa kolom
data = {
    'index':[],
    'prabowo_subianto_Negatif': [],
    'prabowo_subianto_Neutral': [],
    'prabowo_subianto_Positif': []
}
df_etk_ps = pd.DataFrame(data)

# Melakukan concat
dataps = pd.concat([df_etk_ps,data_ps],ignore_index=True)
# Melakukan rename koom 
dataps.rename(columns={'prabowo_subianto_Negatif':'Negatif','prabowo_subianto_Neutral': 'Neutral','prabowo_subianto_Positif':'Positif'}, inplace=True)
# Melakukan unpivot
unp_ps= pd.melt(dataps, id_vars=['index'], var_name='prabowo_subianto', value_name='Value')
# Menghapus baris dengan nilai selain "Positif", "Negatif", dan "Netral" di kolom "Sentimen"
allowed_values = ['Positif', 'Negatif', 'Neutral']
unp_ps = unp_ps.loc[unp_ps['prabowo_subianto'].isin(allowed_values)]
unp_ps=unp_ps.dropna()

# Mengubah tipe data
unp_ps['index']=unp_ps['index'].astype(int)
unp_ps['Value']=unp_ps['Value'].astype(int)
unp_ps

# save data
unp_ps.to_excel("../gerak kinetik/result_script/Sentimen_PS.xlsx",index=False)

# ANIES BASWEDAN

# Melakukan one-hot encoding menggunakan pd.get_dummies
one_hot_encoded3 = pd.get_dummies(data1, columns=['anies_baswedan'], dtype='int')
# Mengambil kolom yang diperlukan
data_ab = one_hot_encoded3[['index'] + list(one_hot_encoded3.columns[-3:])]

# Buat DataFrame dengan beberapa kolom
data = {
    'index':[],
    'anies_baswedan_Negatif': [],
    'anies_baswedan_Neutral': [],
    'anies_baswedan_Positif': []
}
df_etk_ab = pd.DataFrame(data)

# Melakukan concat
dataAB = pd.concat([df_etk_ab,data_ab],ignore_index=True)
# Melakukan rename koom 
dataAB.rename(columns={'anies_baswedan_Negatif':'Negatif','anies_baswedan_Neutral': 'Neutral','anies_baswedan_Positif':'Positif'}, inplace=True)
# Melakukan unpivot
unp_ab= pd.melt(dataAB, id_vars=['index'], var_name='anies_baswedan', value_name='Value')
# Menghapus baris dengan nilai selain "Positif", "Negatif", dan "Netral" di kolom "Sentimen"
allowed_values = ['Positif', 'Negatif', 'Neutral']
unp_ab = unp_ab.loc[unp_ab['anies_baswedan'].isin(allowed_values)]
unp_ab=unp_ab.dropna()

# Mengubah tipe data
unp_ab['index']=unp_ab['index'].astype(int)
unp_ab['Value']=unp_ab['Value'].astype(int)

# save data
unp_ab.to_excel("../gerak kinetik/result_script/Sentimen_AB.xlsx",index=False)

# KONSTITUENSI
# 1. Spektrum Politik
kons_spektrum_politik=data1[['index','spektrum_politik']]

# Use the explode function to create a new row for each category in the list
df = kons_spektrum_politik.explode('spektrum_politik')
# Use get_dummies to create dummy variables
dummies = pd.get_dummies(df, columns=['spektrum_politik'], prefix='Category')
# Group by the ID and sum the dummy variables for each category
dummies = dummies.groupby('index').sum()
# Reset the index to get the 'ID' back as a column
dummies = dummies.reset_index()
sp = dummies

# Buat DataFrame dengan beberapa kolom
data = {
    'index':[],
    'Category_Kultural': [],
    'Category_Nasionalis': [],
    'Category_Pragmatis': []
}
new_sp = pd.DataFrame(data)

# Melakukan COncat
data_sp = pd.concat([new_sp,sp],ignore_index=True)
# Melakukan rename kolom 
data_sp.rename(columns={'Category_Kultural':'Kultural','Category_Nasionalis': 'Nasionalis','Category_Pragmatis':'Pragmatis'}, inplace=True)

# data_sp.to_excel('C:/Dattabot/Dashboard Agenda Kinetik/onehot_spek_pol.xlsx')
# Melakuka unpivot kolom
unp_spek_pol= pd.melt(data_sp, id_vars=['index'], var_name='spektrum_pol', value_name='Value')

# Menghapus baris dengan nilai selain 'Kultural', 'Nasionalis', 'Pragmatis'
allowed_values = ['Kultural', 'Nasionalis', 'Pragmatis']
unp_spek_pol = unp_spek_pol.loc[unp_spek_pol['spektrum_pol'].isin(allowed_values)]
unp_spek_pol = unp_spek_pol.dropna()
# Menghapus kolom yang tidak diperlukan
unp_spek_pol['index']=unp_spek_pol['index'].astype(int)
unp_spek_pol['Value']=unp_spek_pol['Value'].astype(int)

# Save data 
unp_spek_pol.to_excel("../gerak kinetik/result_script/jenis_partai.xlsx", index=False)

# 2. Pekerjaan
# Mengambil kolom yang diperlukan
kons_pekerjaan=data1[['index','profesi']]
# Use the explode function to create a new row for each category in the list
df = kons_pekerjaan.explode('profesi')
# Use get_dummies to create dummy variables
dummies = pd.get_dummies(df, columns=['profesi'], prefix='Category')
# Group by the ID and sum the dummy variables for each category
dummies = dummies.groupby('index').sum()
# Reset the index to get the 'ID' back as a column
dummies = dummies.reset_index()
pekerjaan = dummies

# Buat DataFrame dengan beberapa kolom
data = {
    'index':[],
    'Category_Pertanian & Perikanan': [],
    'Category_Pertambangan': [],
    'Category_Manufaktur': [],
    'Category_Pengelolaan Air, Sampah, Listrik, & Gas': [],
    'Category_Konstruksi & Transportasi': [],
    'Category_ASN': [],
    'Category_Pendidikan & Kesehatan': [],
    'Category_Mamin, Informasi, & Komunikasi': [],
    'Category_Perdagangan': [],
    'Category_Jasa Keuangan Asuransi & Bisnis': [],
    'Category_Lainnya': []
}
new_peke = pd.DataFrame(data)
# Melakukan concat
data_pekerjaan = pd.concat([new_peke,pekerjaan],ignore_index=True)
# Melakukan rename kolom 
data_pekerjaan.rename(columns={
    'Category_Pertanian & Perikanan': 'Pertanian & Perikanan',
    'Category_Pertambangan': 'Pertambangan',
    'Category_Manufaktur': 'Manufaktur',
    'Category_Pengelolaan Air, Sampah, Listrik, & Gas': 'Pengelolaan Air, Sampah, Listrik, & Gas',
    'Category_Konstruksi & Transportasi': 'Konstruksi & Transportasi',
    'Category_ASN': 'ASN',
    'Category_Pendidikan & Kesehatan': 'Pendidikan & Kesehatan',
    'Category_Mamin, Informasi, & Komunikasi': 'Makanan, Minuman, Informasi & Komunikasi',
    'Category_Perdagangan': 'Perdagangan',
    'Category_Jasa Keuangan Asuransi & Bisnis': 'Jasa Keuangan Asuransi & Bisnis',
    'Category_Lainnya': 'Lainnya'
}, inplace=True)

# Melakukan unpivot kolom
unp_peker= pd.melt(data_pekerjaan, id_vars=['index'], var_name='profesi', value_name='Value')
# Menghapus baris dengan nilai selain 'Kultural', 'Nasionalis', 'Pragmatis'
allowed_values = ['Pertanian & Perikanan', 'Pertambangan', 'Manufaktur',
       'Pengelolaan Air, Sampah, Listrik, & Gas', 'Konstruksi & Transportasi',
       'ASN', 'Pendidikan & Kesehatan', 'Media, Informasi, & Komunikasi',
       'Perdagangan', 'Jasa Keuangan Asuransi & Bisnis', 'Lainnya']
unp_peker = unp_peker.loc[unp_peker['profesi'].isin(allowed_values)]
unp_peker=unp_peker.dropna()
# Mengambil kolom yang diperlukan
unp_peker['index']=unp_peker['index'].astype(int)
unp_peker['Value']=unp_peker['Value'].astype(int)

# save data 
unp_peker.to_excel("../gerak kinetik/result_script/jenis_pekerjaan.xlsx", index=False)

# 3. Generasi 
kons_generasi=data1[['index','generasi']]
# Use the explode function to create a new row for each category in the list
df = kons_generasi.explode('generasi')
# Use get_dummies to create dummy variables
dummies = pd.get_dummies(df, columns=['generasi'])
# Group by the ID and sum the dummy variables for each category
dummies = dummies.groupby('index').sum()
# Reset the index to get the 'ID' back as a column
dummies = dummies.reset_index()
# Display the result
generasi = dummies

# Buat DataFrame dengan beberapa kolom
data = {
    'index':[],
    'generasi_Alpha & Gen Z': [],
    'generasi_Gen X': [],
    'generasi_Gen Y': [],
    'generasi_Baby Boomers': []
}
new_gen = pd.DataFrame(data)
# Melakukan concat
data_gen = pd.concat([new_gen,generasi],ignore_index=True)
# Melakukan rename kolom
data_gen.rename(columns={
    'generasi_Alpha & Gen Z':'Alpha & Gen Z',
    'generasi_Gen X':'Gen X',
    'generasi_Gen Y':'Gen Y',
    'generasi_Baby Boomers':'Baby Boomers'
    }, inplace=True)
# Melakukan unpivot kolom
unp_gen= pd.melt(data_gen, id_vars=['index'], var_name='generasi', value_name='Value')

# Menghapus baris dengan nilai selain 'Kultural', 'Nasionalis', 'Pragmatis'
allowed_values = ['Alpha & Gen Z', 'Gen X', 'Gen Y', 'Baby Boomers']
unp_gen = unp_gen.loc[unp_gen['generasi'].isin(allowed_values)]
unp_gen=unp_gen.dropna()
# Mengubah tipe kolom
unp_gen['index']=unp_gen['index'].astype(int)
unp_gen['Value']=unp_gen['Value'].astype(int)

# Save data 
unp_gen.to_excel("../gerak kinetik/result_script/generasi.xlsx", index=False)

# 4. Pendidikan
kons_pend=data1[['index','pendidikan']]
# Use the explode function to create a new row for each category in the list
df = kons_pend.explode('pendidikan')
# Use get_dummies to create dummy variables
dummies = pd.get_dummies(df, columns=['pendidikan'])
# Group by the ID and sum the dummy variables for each category
dummies = dummies.groupby('index').sum()
# Reset the index to get the 'ID' back as a column
dummies = dummies.reset_index()
# Display the result
pendidikan = dummies

# Buat DataFrame dengan beberapa kolom
data = {
    'index':[],
    'pendidikan_Tidak Sekolah': [],
    'pendidikan_SD': [],
    'pendidikan_SMP': [],
    'pendidikan_SMA': [],
    'pendidikan_Perguruan Tinggi': []
}
new_pend = pd.DataFrame(data)
# Melakukan concat
data_pend = pd.concat([new_pend,pendidikan],ignore_index=True)
# Rename kolom
data_pend.rename(columns={
    'pendidikan_Tidak Sekolah':'Tidak Sekolah',
    'pendidikan_SD':'SD',
    'pendidikan_SMP':'SMP',
    'pendidikan_SMA':'SMA',
    'pendidikan_Perguruan Tinggi':'Perguruan Tinggi'
    }, inplace=True)

# Melakukan unpivot kolom
unp_pend= pd.melt(data_pend, id_vars=['index'], var_name='pendidikan', value_name='Value')

# Menghapus baris dengan nilai selain 'Kultural', 'Nasionalis', 'Pragmatis'
allowed_values = ['Tidak Sekolah', 'SD', 'SMP', 'SMA', 'Perguruan Tinggi']
unp_pend = unp_pend.loc[unp_pend['pendidikan'].isin(allowed_values)]
unp_pend=unp_pend.dropna()
# Mengubah tipe data
unp_pend['index']=unp_pend['index'].astype(int)
unp_pend['Value']=unp_pend['Value'].astype(int)

# Save data
unp_pend.to_excel("../gerak kinetik/result_script/pendidikan.xlsx")

# 5. Regional 
kons_regional=data1[['index','regional']]

# Use the explode function to create a new row for each category in the list
df = kons_regional.explode('regional')
# Use get_dummies to create dummy variables
dummies = pd.get_dummies(df, columns=['regional'])
# Group by the ID and sum the dummy variables for each category
dummies = dummies.groupby('index').sum()
# Reset the index to get the 'ID' back as a column
dummies = dummies.reset_index()
# Merge the dummy variables back with the original DataFrame
#generasi = pd.merge(df, dummies, on='index')
# Display the result
regional = dummies
# Buat DataFrame dengan beberapa kolom
data = {
    'index':[],
    'regional_Jawa': [],
    'regional_Sumatera': [],
    'regional_Kalimantan': [],
    'regional_Sulawesi': [],
    'regional_Bali & Nusa Tenggara': [],
    'regional_Maluku & Papua': []
}
new_reg = pd.DataFrame(data)
# Melakukan concat
data_reg = pd.concat([new_reg,regional],ignore_index=True)
# Melakukan rename kolom
data_reg.rename(columns={
    'regional_Jawa':'Jawa',
    'regional_Sumatera':'Sumatera',
    'regional_Kalimantan':'Kalimantan',
    'regional_Sulawesi':'Sulawesi',
    'regional_Bali & Nusa Tenggara':'Bali & Nusa Tenggara',
    'regional_Maluku & Papua':'Maluku & Papua'
    }, inplace=True)
# Unpivot kolom
unp_reg= pd.melt(data_reg, id_vars=['index'], var_name='regional', value_name='Value')
# Menghapus baris dengan nilai selain 'Kultural', 'Nasionalis', 'Pragmatis'
allowed_values = ['Jawa', 'Sumatera', 'Kalimantan', 'Sulawesi',
       'Bali & Nusa Tenggara', 'Maluku & Papua']
unp_reg = unp_reg.loc[unp_reg['regional'].isin(allowed_values)]
unp_reg=unp_reg.dropna()

# Mengubah tipe data
unp_reg['index']=unp_reg['index'].astype(int)
unp_reg['Value']=unp_reg['Value'].astype(int)

# Save data
unp_reg.to_excel("../gerak kinetik/result_script/regional.xlsx")

# 6. Masyarakat
kons_masy=data1[['index','kategori_desa_kota']]
# Use the explode function to create a new row for each category in the list
df = kons_masy.explode('kategori_desa_kota')
# Use get_dummies to create dummy variables
dummies = pd.get_dummies(df, columns=['kategori_desa_kota'])
# Group by the ID and sum the dummy variables for each category
dummies = dummies.groupby('index').sum()
# Reset the index to get the 'ID' back as a column
dummies = dummies.reset_index()
# Merge the dummy variables back with the original DataFrame
#generasi = pd.merge(df, dummies, on='index')
# Display the result
masyarakat = dummies

# Buat DataFrame dengan beberapa kolom
data = {
    'index':[],
    'kategori_desa_kota_Pedesaan': [],
    'kategori_desa_kota_Perkotaan': []
}
new_masy = pd.DataFrame(data)
# concat
data_masy = pd.concat([new_masy,masyarakat],ignore_index=True)
# rename kolom
data_masy.rename(columns={
    'regional_Jawa':'Jawa',
    'kategori_desa_kota_Pedesaan':'Pedesaan',
    'kategori_desa_kota_Perkotaan':'Perkotaan',
    }, inplace=True)

# Unpivot kolom
unp_masy= pd.melt(data_masy, id_vars=['index'], var_name='masyarakat', value_name='Value')
# Menghapus baris dengan nilai selain 'Kultural', 'Nasionalis', 'Pragmatis'
allowed_values = ['Pedesaan','Perkotaan']
unp_masy = unp_masy.loc[unp_masy['masyarakat'].isin(allowed_values)]
unp_masy=unp_masy.dropna()
# Mengubah tipe kolom
unp_masy['index']=unp_masy['index'].astype(int)
unp_masy['Value']=unp_masy['Value'].astype(int)

# Save data
unp_masy.to_excel("../gerak kinetik/result_script/masyarakat.xlsx")

