from . import application
import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from html.parser import HTMLParser
from io import StringIO

nltk.download('stopwords')
nltk.download('punkt')

import json
import pandas as pd
import os


class Classifier:

    @staticmethod
    def load_scheme_indicators():
    
        with open(os.path.join(application.config['DATA'], 'scheme_indicators.json'), encoding='utf-8') as scjson:
            indicators_json = json.load(scjson)
            
        return indicators_json

    @staticmethod
    def stem_original_txt(porter, original_text):
        
        token_words = word_tokenize(original_text)
        stem_sentence = []
        word_df = pd.DataFrame(columns = ['original', 'stemmed'])
        
        for word in token_words:
            stem = porter.stem(word)
            
            if word.endswith("ly") and stem.endswith("li"):
                stem = stem.replace("li", "")
                
            word_df = word_df.append({'original': word, 'stemmed': stem}, ignore_index=True)
        
        return word_df
        
    @staticmethod
    def stem_indicator(porter, indicator):
        no_stopwords = []
        indicator_tokens = word_tokenize(indicator)
        no_stopwords = [word for word in indicator_tokens if not word in stopwords.words()]
        
        if len(no_stopwords) == 0:
            no_stopwords = indicator_tokens
            
        stemmed_ind = []
        
        for word in no_stopwords:
            stemmed_ind.append(porter.stem(word))
            
        return stemmed_ind
    
    @staticmethod
    def search_indicator_in_text(word_df, stemmed_ind):
        word_df = word_df.reset_index()
        positions = []

        found = False
        for i, row in word_df.iterrows():
            j = 0
            k = i
            while j<len(stemmed_ind) and word_df.iloc[i]['stemmed'] == stemmed_ind[j]:
                j = j + 1
                k = k + 1

            if j == len(stemmed_ind):
                found = True
                positions.append(str(i) + ',' + str(k))
            
        return found, positions
        
    @staticmethod
    def process_i_nodes(data):
        i_node_dict = dict()
        
        inodes = [(x['nodeID'], x['text']) for x in data['AIF']['nodes'] if x['type'] == 'I']
        
        for i in inodes:
            itok = ' '.join(word_tokenize(i[1].lower()))
            i_node_dict[i[0]] = itok
    
        return i_node_dict
        
    @staticmethod
    def search_txt_in_inodes(txtval, i_node_dict):
        for nodeID in i_node_dict:
            i_text = i_node_dict[nodeID]
            if txtval in i_text:
                return nodeID
                
        return ""

    @staticmethod
    def get_incoming_RAs(inodeID, data, scheme):
        incomingIDs = [x['fromID'] for x in data['AIF']['edges'] if x['toID'] == inodeID]
        ranodes = [y['nodeID'] for y in data['AIF']['nodes'] if y['type'] == 'RA' and y['nodeID'] in incomingIDs ]
        
        for raID in ranodes:
            d = next(node for node in data['AIF']['nodes'] if node['nodeID'] == raID)
            d['text'] = scheme
            d['scheme'] = scheme
        
        return data
        
    @staticmethod
    def get_outgoing_RAs(inodeID, data, scheme):
        outgoingIDs = [x['toID'] for x in data['AIF']['edges'] if x['fromID'] == inodeID]
        ranodes = [y['nodeID'] for y in data['AIF']['nodes']  if y['type'] == 'RA' and y['nodeID'] in outgoingIDs ]
        
        for raID in ranodes:
            d = next(node for node in data['AIF']['nodes'] if node['nodeID'] == raID)
            d['text'] = scheme
            d['scheme'] = scheme
        
        return data


    @staticmethod
    def type_RAs(self, word_df, positions, data, scheme, i_node_dict):
        for p in positions:
            pos = p.split(',')
            start = int(pos[0])
            end = int(pos[1])
            
            #check text before indicator
            start_bkw = start - 8
            if(start_bkw >= 0):
                text_before_ind = word_df['original'].iloc[start_bkw : start-3]
                text1 = ' '.join(text_before_ind)
                nodeID1 = self.search_txt_in_inodes(text1, i_node_dict)
                if(nodeID1 != ""):
                    data = self.get_outgoing_RAs(nodeID1, data, scheme)
                    
                
            #check text after indicator
            end_fwd = end + 5
            if(end_fwd < word_df.size):
                text_after_ind = word_df['original'].iloc[end + 1 : end_fwd]
                text2 = ' '.join(text_after_ind)
                nodeID2 = self.search_txt_in_inodes(text2, i_node_dict)
                if(nodeID2 != ""):
                    data = self.get_incoming_RAs(nodeID2, data, scheme)

            #check text around indicator
            start_around = start - 2
            end_around = end + 3
            if(start_around >= 0 and end_around < word_df.size) :
                text_around_ind = word_df['original'].iloc[start_around : end_around]
                text3 = ' '.join(text_around_ind)
                nodeID3 = self.search_txt_in_inodes(text3, i_node_dict)
                
                if(nodeID3 != ""):
                    data = self.get_incoming_RAs(nodeID3, data, scheme)
                    data = self.get_outgoing_RAs(nodeID3, data, scheme)

            return data
            
    @staticmethod
    def strip_tags(html):
        s=MLStripper()
        s.feed(html)
        return s.get_data()
        
    
    @staticmethod
    def identify_schemes(self, data):
        porter = PorterStemmer()
        
        i_node_dict = self.process_i_nodes(data)
        
        schemeindicators = self.load_scheme_indicators()['scheme indicators']
        original_text = data['text']['txt']
        
        original_text = self.strip_tags(original_text)
        
        
        word_df = self.stem_original_txt(porter, original_text.lower())
        
        for scheme in schemeindicators:
       
            for ind in scheme['indicators']:
                
                stemmed_ind = self.stem_indicator(porter, ind)
                found, positions = self.search_indicator_in_text(word_df, stemmed_ind)
              
                if found == True:
                    data = self.type_RAs(self, word_df, positions, data, scheme['scheme'], i_node_dict)
        
        return data
        

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()
    
    def handle_data(self, d):
        self.text.write(d)
        
    def get_data(self):
        return self.text.getvalue()
