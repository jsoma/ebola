import proofread as prf
import pandas as pd
import sys
import glob
import csv

COUNTRIES = [
    {
        'path': "../drcongo_data/csv",
        'name': "Democratic Republic of the Congo",
        'filenames': "*.csv",
        'output': "compiled/drc.csv"
    },
    {
        'path': "../guinea_data",
        'name': "Guinea",
        'filenames': "ebola_guinea_*.csv",
        'output': 'compiled/guinea.csv'
    },
    {
        'path': "../liberia_data",
        'name': "Liberia",
        'filenames': "*.csv",
        'output': 'compiled/libera.csv'
    },
    {
        'path': "../sl_data",
        'name': "Sierra Leone",
        'filenames': "*.csv",
        'output': 'compiled/sierra-leone.csv'
    }
]

class CountryCSV:
    
    
    def __init__(self, data):
        self.path = data['path']
        self.name = data['name']
        self.filenames = data['filenames']
        self.output_filename = data['output']
        
        
    def log(self, content):
        print content
        
    
    def open_files(self):
        filenames = self.proofread_filenames()
        self.files = [open(filename, 'rU') for filename in filenames]
        self.dict_readers = [csv.DictReader(file) for file in self.files]
    
    
    def close_files(self):
        for file in self.files:
            file.close()
            
    
    def fieldnames(self):
        try:
            return self.headers
        except AttributeError:
            # Get unique field names across all CSV files
            fieldnames = list(set([item for sublist in (reader.fieldnames for reader in self.dict_readers) for item in sublist]))
            # Put date, variable and country name first
            self.headers = sorted(fieldnames, key=lambda fieldname: fieldname.lower() not in ['date','variable','description'])
            return self.headers
        
        
    def write(self):
        self.log("\033[1m## Processing %s...\033[0m" % self.name)
        self.log("Writing standard version")

        self.open_files()
        fieldnames = self.fieldnames()
        
        with open(self.output_filename, 'w') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            dict_writer.writeheader()
            for reader in self.dict_readers:
                for row in reader:
                    dict_writer.writerow(row)

        self.close_files()
        self.write_stacked()

        self.log("Complete, %s files compiled to \033[1m%s\033[0m\n" % (len(self.files), self.output_filename))


    # Will need to be revised in the future once we pull variables together
    def write_stacked(self):
        self.log("Writing stacked version")
        headers = self.fieldnames()
        df = pd.read_csv(self.output_filename)
        location_columns = (df.columns - ['date', 'Date', 'variable', 'Variable', 'Description', 'description'])
        var_col = (set(prf.VARIABLE_COL_NAMES) & set(headers)).pop()
        date_col = (set(prf.DATE_COL_NAMES) & set(headers)).pop()

        stacked = pd.melt(df,
            id_vars=[var_col, date_col],
            value_vars=list(location_columns),
            var_name='Location',
            value_name='Value'
            ).sort([date_col, 'Location'])

        stacked_filename = self.output_filename.replace(".csv","-stacked.csv")
        stacked.to_csv(stacked_filename)
        

    def proofread_filenames(self):
        passed = []
        failed = []
        
        filepaths = "%s/%s" % (self.path, self.filenames)
        
        for filename in glob.glob(filepaths):
            if prf.proofread(filename, verbose=False):
                passed.append(filename)
            else:
                failed.append(filename)

        if len(failed) > 0:
            self.log("The following file(s) failed proofreading and will not be compiled:")
            self.log("%s" % "\n".join(failed))

        return passed
        

for country_data in COUNTRIES:
    country_csv = CountryCSV(country_data)
    country_csv.write()