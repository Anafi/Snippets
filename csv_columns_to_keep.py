# A script to clean a large csv file and keep the columns a user is interested in

csv_path='C:\Users\.....csv'
res_csv_path='C:\Users\...new.csv'
import csv

with open(csv_path,"rb") as source:
    rdr= csv.reader( source )
    with open(res_csv_path,"wb") as result:
        wtr= csv.writer( result )
        for r in rdr:
            # here you specify the columns to be written in a new csv based on index
            wtr.writerow( (r[0], r[1], r[6], r[8], r[9], r[50]))