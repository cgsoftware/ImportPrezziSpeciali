# -*- encoding: utf-8 -*-

import math

from osv import fields,osv
import ir
import pooler
import tools
import time
from tools.translate import _
import base64
from tempfile import TemporaryFile
import csv
import sys
import os
import re


class import_prezzi(osv.osv_memory):
    _name = 'import.prezzi'
    _description = 'Importa Prezzi Speciali '
    _columns = {
                'data': fields.binary('File csv di Import', required=True),
                }

    def import_prezzi_func(self, cr, uid, ids, context=None):
        import_data = self.browse(cr, uid, ids)[0]
        cerca =[]
        fileobj = TemporaryFile('w+')
        fileobj.write(base64.decodestring(import_data.data))
        fileobj.seek(0)
        testo_log = """Inizio procedura di Importazione Prezzi Speciali """ + time.ctime() + '\n'
        error = False
        nome =''
        for riga in  fileobj.readlines():
            nome =''
            #import pdb;pdb.set_trace()
            riga = riga.replace('"', '')
            riga = riga.replace('\n', '')
            riga = riga.replace(',', '.')
            riga = riga.split(";")
            error = False
            cli_id = False
            art_id =False
            categ_id = False
            cli_id = self.pool.get('res.partner').search(cr,uid,[('ref','=',riga[0]),('customer','=',1)])
            if not cli_id:
                testo_log = testo_log + " Cliente  " + riga[0] + " NON TROVATO \n"
                error = True
                 
            else:
                cerca += [('partner_id','=',cli_id[0])]
                nome += 'cli' + riga[0]
            if riga[1]: # c'è un codice articolo ad-hoc
                    art_id = self.pool.get('product.product').search(cr,uid,[('adhoc_code','=',riga[1])])
                    if not art_id:
                        testo_log = testo_log + " Articolo Ad-Hoc  " + riga[1] + " NON TROVATO \n"
                        error = True
                    else:
                        cerca += [('partner_id','=',art_id[0])]
                        nome += 'art '+ riga[1]
                        
            if riga[2]: # c'è un articolo openerp
                  art_id = self.pool.get('product.product').search(cr,uid,[('default_code','=',riga[2])])  
                  if not art_id:
                      testo_log = testo_log + " Articolo OpenErp   " + riga[1] + " NON TROVATO \n"
                      error = True
                  else:
                      cerca += [('partner_id','=',art_id[0])]
                      nome += 'art '+ riga[2]
            if riga[3]: # c'è una categoria
                    categ_id = self.pool.get('product.category').search(cr,uid,[('name','ilike',riga[3])])
                    if not categ_id:
                        testo_log = testo_log + " Categoria  " + riga[3] + " NON TROVATO \n"
                        error = True
                    else:
                        cerca += [('partner_id','=',categ_id[0])]
                        nome += 'cat '+ riga[3]
            if not error:
                if len(cerca):
                    prezzo_id = self.pool.get('product.pricelist.item').search(cr,uid,cerca)
                    if prezzo_id: # ho trovato una riga quind deve fare solo aggiornamenti
                        prezzo = {}
                        if riga[5]:
                          # riga[5] = riga.replace(',', '.')
                           prezzo.update({'price_surcharge':riga[5]})
                        if riga[4]:
                           riga[4]=riga[4]/100
                           prezzo.update({'price_discount':riga[4]})
                        ok = self.pool.get('product.pricelist.item').wite(cr,uid,prezzo_id,prezzo)

                    else:
                        # Scrive un solo record
                        prezzo = {}
                        prezzo.update({'name':nome})
                        if cli_id:
                             prezzo.update({'partner_id':cli_id[0]})
                             ver_listino_id = self.pool.get('res.partner').browse(cr,uid,cli_id[0]).property_product_pricelist
                             #import pdb;pdb.set_trace()
                             # version_id[0].id presa la prima riga della versione listino ver_listino_id.version_id[0].id
                             if ver_listino_id:
                                ver_listino_id= ver_listino_id.version_id[0].id
                                prezzo.update({'price_version_id':ver_listino_id})
                                prezzo.update({'base':1})
                                if riga[5]:
                                    prezzo.update({'price_surcharge':riga[5]})
                                if riga[4]:
                                    riga[4]=float(riga[4])/100
                                    prezzo.update({'price_discount':riga[4]})
                                if art_id:
                                 prezzo.update({'product_id':art_id[0]})
                                if categ_id:
                                 prezzo.update({'categ_id':categ_id[0]})
                                prezzo_id = self.pool.get('product.pricelist.item').create(cr,uid,prezzo)
                        
                    
                 
        testo_log = testo_log + " Operazione Teminata  alle " + time.ctime() + "\n"
        #invia e-mail
        type_ = 'plain'
        tools.email_send('OpenErp@mainettiomaf.it',
                       ['Giuseppe.Sciacco@mainetti.com','g.dalo@cgsoftware.it'],
                       'Esito Importazione Prezzi Articoli',
                       testo_log,
                       subtype=type_,
                       )

                
            
        
        return   {'type': 'ir.actions.act_window_close'}  

import_prezzi()