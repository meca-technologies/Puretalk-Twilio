import logging
from flask import Flask, json, jsonify, request
import config

import json
import datetime
import requests
import math

import pymongo
from bson.objectid import ObjectId

from twilio.twiml.voice_response import VoiceResponse, Connect, Gather
from twilio.rest import Client

# setting up logging
logger = logging.getLogger('PureTalk-Twilio')

logger.setLevel(logging.DEBUG)

todayFormatted = (datetime.datetime.today()).strftime("%Y-%m-%d")

fh = logging.FileHandler('logs/puretalk-twilio-{}.py.log'.format(todayFormatted))
fh.setLevel(logging.DEBUG)

formatter = logging.Formatter("[%(asctime)s] - %(name)14s - %(levelname)8s | %(message)s","%Y-%m-%d %H:%M:%S")
fh.setFormatter(formatter)

logger.addHandler(fh)

app = Flask(__name__)
app.secret_key = '2abceVR5ENE7FgMxXdMwuzUJKC2g8xgy'

app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

@app.route('/recording/callback', methods=['POST'])
def upload_recording():
    try:
        logger.debug('Got Call Back: {}'.format(str(request.form)))
        recording_url = request.form['RecordingUrl']
        logger.debug('\t Recording URL: {}'.format(str(recording_url)))

        call_id = request.form['CallSid']
        logger.debug('\t Call SID Recording: {}'.format(str(call_id)))

        recording_sid = request.form['RecordingSid']
        logger.debug('\t Recording SID: {}'.format(str(recording_sid)))

        updateData = {
            'recording_id':recording_sid,
            'recording_link':recording_url
        }
        logger.debug('\t Update Data: {}'.format(str(updateData)))
        try:
            client = pymongo.MongoClient("mongodb+srv://admin:QM6icvpQ6SlOveul@cluster0.vc0rw.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
            mongoDB = client['jamesbon']
            leads_col = mongoDB['leads']
            search_query = {
                "call_logs.call_id":call_id
            }
            update_query = {
                "$set": {
                    "call_logs.$.recording_id": recording_sid,
                    "call_logs.$.recording_link": recording_url,
                    'updated_at':str(datetime.datetime.utcnow())[:-7]
                }
            }
            leads_col.update_one(search_query, update_query)
            leadRow = leads_col.find_one(search_query)
            logger.debug('\t Committed Data')
            client.close()
            try:
                recording_status = request.form['RecordingStatus']
                if leadRow['status'] == 'voicemail':
                    recording_status = 'voicemail'
                elif leadRow['status'] == 'no-answer':
                    recording_status = 'no-answer'
                call_event = {
                    'CallStatus':recording_status,
                    'ParentCallSid':request.form['CallSid'],
                    'CallSid':request.form['CallSid'],
                    'CallDuration':request.form['RecordingDuration'],
                }
                url = '{}calls/events'.format(config.webhooks)
                requests.post(url, data=call_event)
            except:
                pass
        except:
            try:
                client.close()
            except:
                pass
            pass
    except:
        logger.error('Got Nothing')
        pass
    return jsonify({"Message":"Success"})

@app.route('/calls/events', methods=['POST'])
def updateStatus():
    try:
        logger.debug('Call Events Data: {}'.format(str(request.form)))
        client = pymongo.MongoClient("mongodb+srv://admin:QM6icvpQ6SlOveul@cluster0.vc0rw.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        mongoDB = client['jamesbon']
        leads_col = mongoDB['leads']
        campaigns_col = mongoDB['campaigns']
        company_billing_col = mongoDB['company_billing']
        wallet_transactions_col = mongoDB['wallet_transactions']
        try:
            try:
                call_status = request.form['CallStatus']
                logger.debug('\t Call Status: {}'.format(str(call_status)))
            except:
                return jsonify({"Message":"Success"}) 

            call_id_child = request.form['CallSid']
            logger.debug('\t CHILD Call SID: {}'.format(str(call_id_child)))

            try:
                call_id = request.form['ParentCallSid']
                logger.debug('\t Call SID: {}'.format(str(call_id)))
            except:
                call_id = request.form['CallSid']
                logger.debug('\t CHILD Call SID: {}'.format(str(call_id)))
            
            search_query = {
                "call_logs.call_id":call_id
            }
            logger.debug('\t Search Query: {}'.format(str(search_query)))
            update_query = {
                "$set": {
                    'call_logs.$.call_id_child':call_id_child,
                    'updated_at':str(datetime.datetime.utcnow())[:-7]
                }
            }
            logger.debug('\t Update Data: {}'.format(str(update_query)))
            logger.debug('\t Stage Data')
            leadRow = leads_col.find_one(search_query)
            if leadRow['status'] == 'voicemail':
                call_status = 'voicemail'
            elif leadRow['status'] == 'no-answer':
                call_status = 'no-answer'
            leads_col.update_one(search_query, update_query)
            logger.debug('\t Committed Data')

            logger.debug('\t Grabbed Lead Row')

            logger.debug('\t Lead ID: {}'.format(str(leadRow['_id'])))
            update_query = {
                "$set": {}
            }
            try:
                print(call_status)
            except:
                logger.error('\t\t Failed Getting call_status')
            try:
                print(str(datetime.datetime.utcnow())[:-7])
            except:
                logger.error('\t\t Failed Getting DATETIME')
            try:
                if leadRow['call_logs'][len(leadRow['call_logs'])-1]['status'] != 'voicemail':
                    update_query = {
                        "$set": {
                            'call_logs.$.status':call_status,
                            'call_logs.$.updated_at':str(datetime.datetime.utcnow())[:-7],
                            'updated_at':str(datetime.datetime.utcnow())[:-7],
                            'status':call_status
                        }
                    }
                else:
                    update_query = {
                        "$set": {
                            'call_logs.$.updated_at':str(datetime.datetime.utcnow())[:-7],
                            'updated_at':str(datetime.datetime.utcnow())[:-7],
                            'status':call_status
                        }
                    }
            except:
                logger.error('\t\t Failed Writing update query')
            try:
                update_query["$set"]["call_logs.$.time_taken"] = getInt(request.form['CallDuration'])
                update_query["$set"]["time_taken"] = getInt(request.form['CallDuration'])
            except:
                pass
            try:
                if leadRow['status'] == 'voicemail':
                    call_status = 'voicemail'
                elif leadRow['status'] == 'no-answer':
                    call_status = 'no-answer'
            except:
                pass
            if call_status == 'completed' or call_status == 'voicemail':
                logger.debug('\t\t Call Finished Need to charge them')
                campaign_id = leadRow['campaign_id']
                logger.debug('\t\t Need to charge {}'.format(str(campaign_id)))
                campaignRow = campaigns_col.find_one({'_id':campaign_id})
                company_id = campaignRow['company_id']
                logger.debug('\t\t With company id {}'.format(str(company_id)))
                billing = company_billing_col.find_one({'company_id':company_id})
                if billing:
                    if call_status != 'voicemail':
                        logger.debug('\t\t Biller Found')
                        charge_amount = getDecimal(billing['charge_amount'])
                        logger.debug('\t\t Charge Amount: {}'.format(str(charge_amount)))

                        charge_type = getInt(billing['charge_type'])
                        logger.debug('\t\t Charge Type: {}'.format(str(charge_type)))
                        walletData = {}
                        call_duration = getInt(request.form['CallDuration'])
                        if charge_type == 0:
                            logger.debug('\t\t Call Duration: {}'.format(str(call_duration)))
                            if call_duration != 0:
                                minutes = getDecimal(math.ceil(call_duration/60))
                                logger.debug('\t\t Call Duration Rounded: {}'.format(str(minutes)))
                                total_charge = getDecimal(charge_amount*minutes)
                                logger.debug('\t\t Total Charge: {}'.format(str(total_charge)))
                                walletData = {
                                    'company_id':company_id,
                                    'type':'charged',
                                    'amount':getDecimal(total_charge)
                                }
                        else:
                            if call_duration > 3:
                                total_charge = getDecimal(charge_amount)
                                logger.debug('\t\t Total Charge: {}'.format(str(total_charge)))
                                walletData = {
                                    'company_id':company_id,
                                    'type':'charged',
                                    'amount':getDecimal(total_charge)
                                }

                        try:
                            walletData['memo'] = 'Campaign ID: {} calling: {}'.format(str(campaign_id), str(leadRow['reference_number']))
                        except:
                            pass
                        logger.debug('\t\t Wallet Data: {}'.format(str(walletData)))
                        logger.debug('\t\t Stage Data')
                        walletData['created_at'] = str(datetime.datetime.utcnow())[:-3]
                        walletData['updated_at'] = str(datetime.datetime.utcnow())[:-3]
                        wallet_transactions_col.insert_one(walletData)
                        #wallet_resp = simpleUpdateRow(wallet_transactions_col, walletData, 'POST')
                        logger.debug('\t\t Committed Data')
                else:
                    logger.error('\t\t Cannot Find Billing')
            #elif call_status == 'answered':
            #    logger.debug('\t Set the call to answered: {}'.format(str(update_query)))
            #    search_query = {
            #        "call_logs.call_id":call_id
            #    }
            #    logger.debug('\t Search Query: {}'.format(str(search_query)))
            #    update_query = {
            #        "$set": {
            #            'call_logs.$.answered':True
            #        }
            #    }
            #    logger.debug('\t Update Data: {}'.format(str(update_query)))
            #    logger.debug('\t Stage Data')
            #    leads_col.update_one(search_query, update_query)

            logger.debug('\t Search Query: {}'.format(str(search_query)))
            logger.debug('\t Lead Update Data: {}'.format(str(update_query)))
            leads_col.update_one(search_query, update_query)
        except:
            pass
        client.close()
    except:
        pass
    return jsonify({"Message":"Success"})

@app.route('/calls/amd', methods=['POST'])
def updateAMD():
    try:
        client = pymongo.MongoClient("mongodb+srv://admin:QM6icvpQ6SlOveul@cluster0.vc0rw.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        mongoDB = client['jamesbon']
        leads_col = mongoDB['leads']
        logger.debug('AMD Data: {}'.format(str(request.form)))
        if request.form['AnsweredBy'] != 'human':
            call_id = request.form['CallSid']
            search_query = {
                "call_logs.call_id":call_id
            }
            lead_row = leads_col.find_one(search_query)
            campaigns_col = mongoDB['campaigns']
            campaign = campaigns_col.find_one({'_id':lead_row['campaign_id']})
            companies_col = mongoDB['companies']
            company = companies_col.find_one({'_id':campaign['company_id']})
            account_sid = company['twilio_account_sid']
            auth_token = company['twilio_auth_token']
            try:
                twilClient = Client(account_sid, auth_token)
                logger.debug('\t Call To Hang Up: {}'.format(str(call_id)))

                logger.debug('\t Attempting To Hang Up Call')
                thisCall = twilClient.calls(call_id).update(twiml='<Response><Hangup/></Response>')
                logger.debug('\t Call Hung Up')
            except:
                pass

            logger.debug('\t Grabbing Lead Info')
            search_query = {
                "call_logs.call_id":str(call_id)
            }
            update_query = {
                "$set": {
                    'call_logs.$.status':'voicemail',
                    'status':'voicemail',
                    'updated_at':str(datetime.datetime.utcnow())[:-7]
                }
            }
            logger.debug('\t Search Query: {}'.format(str(search_query)))
            logger.debug('\t Lead Update Data: {}'.format(str(update_query)))
            leads_col.update_one(search_query, update_query)
            #leadCall = LeadCalls.query.filter(or_(LeadCalls.call_id == call_id, LeadCalls.call_id_child == call_id)).first()
            #leadID = leadCall.lead_id
            #logger.debug('\t Lead ID: {}'.format(leadID))
            #
            #updateData = {
            #    'status':'voicemail'
            #}
            #updateData['updated_at'] = str(datetime.datetime.utcnow())[:-3]
            #logger.debug('\t Lead Update Data: {}'.format(str(updateData)))
            #updateRow = Leads.query.filter_by(id=leadID).update(dict(**updateData))
            #logger.debug('\t Stage Data')
            #db.session.commit()
            logger.debug('\t Committed Data')
        client.close()
    except:
        pass
    return jsonify({"Message":"Success"})

@app.route('/calls/interested', methods=['POST'])
def updateInterest():
    try:
        client = pymongo.MongoClient("mongodb+srv://admin:QM6icvpQ6SlOveul@cluster0.vc0rw.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        mongoDB = client['jamesbon']
        post_data = request.json
        logger.debug('Interest Data: {}'.format(str(request.json)))
        leads_col = mongoDB['leads']

        # Update Lead as interested
        search_query = {
            "call_logs.call_id":post_data['CallSid']
        }
        update_query = {
            '$set':{
                'checked':False,
                'interested':'interested',
                'status':'Completed',
                'updated_at':str(datetime.datetime.utcnow())[:-7]
            }
        }
        leads_col.update_one(search_query,update_query)
        
        # Check for webhook to transfer lead data
        lead = leads_col.find_one(search_query)
        campaigns_col = mongoDB['campaigns']
        campaign = campaigns_col.find_one({'_id':lead['campaign_id']})

        logger.debug('\t Stop recording')
        companies_col = mongoDB['companies']
        company = companies_col.find_one({'_id':campaign['company_id']})
        try:
            try:
                twilio_account_sid = company['twilio_account_sid']
                logger.debug('\t\t Account SID: {}'.format(twilio_account_sid))
            except:
                logger.error('\t\t Failed Grabbing Account SID')
            try:
                twilio_auth_token = company['twilio_auth_token']
                logger.debug('\t\t Auth Token: {}'.format(twilio_auth_token))
            except:
                logger.error('\t\t Failed Grabbing Auth Token')
            try:
                twil_client = Client(twilio_account_sid, twilio_auth_token)
                logger.debug('\t\t Created Twil Client')
            except:
                logger.error('\t\t Failed Creating Twil Client')
            try:
                logger.debug('\t\t Find Recording Using: {}'.format(str(post_data['CallSid'])))
                recording = twil_client.calls(str(post_data['CallSid'])).recordings.list(limit=1)
                try:
                    logger.debug('\t\t Find Total Of {} Recordings'.format(str(len(recording))))
                except:
                    pass
                recording_id = str(recording[0].sid)
                logger.debug('\t\t Recording ID: {}'.format(recording_id))
            except:
                logger.error('\t\t Failed Grabbing Recording ID')
            #try:
            #    twil_client.calls(str(post_data['CallSid'])).recordings(recording_id).update(status='stopped')
            #    logger.debug('\t Stop Record Successful')
            #except:
            #    logger.error('\t\t Failed Sending Stop Request')
        except:
            logger.error('\t Failed to stop recording')
        try:
            ## DO TRANSFER WEBHOOK STUFF #########
             # TEST VARIABLES PASSED
            request_payload = {}
            for data in lead['lead_data']:
                request_payload[data['field_name']] = data['field_value']
            logger.debug('request_payload: {}'.format(str(request_payload)))
            request_url = campaign['xfer_url']

            # HEADER WORK ##########################################
            request_headers = campaign['headers']
            request_headers = delimiterReplace(str(request_headers), request_payload)
            #logger.debug('request_headers: {}'.format(str(request_headers)))
            request_headers = json.loads(request_headers.replace("'", '"'))
            req_headers = {}
            for header in request_headers:
                req_headers[header['field']] = header['value']
            logger.debug('Req_Headers: {}'.format(str(req_headers)))

            # PARAMS WORK ##########################################
            request_params = campaign['params']
            request_params = delimiterReplace(str(request_params), request_payload)
            #logger.debug('Req_URL: {}'.format(str(request_url)))
            request_params = json.loads(request_params.replace("'", '"'))
            if len(request_params) > 0:
                request_url += '?'
                for param in request_params:
                    field = param['field']
                    val = param['value']
                    request_url += f'{field}={val}&'
                request_url = request_url[:-1]
            logger.debug('Req_URL: {}'.format(str(request_url)))


            # PAYLOAD WORK ##########################################
            request_body = campaign['payload']
            request_body = delimiterReplace(str(request_body), request_payload)
            #logger.debug('request_body: {}'.format(str(request_body)))
            request_body = json.loads(request_body.replace("'", '"'))
            logger.debug('Req_Body: {}'.format(str(request_body)))
            #logger.debug('request_payload: {}'.format(str(request_payload)))

            
            request_method = campaign['xfer_method']

            if request_method == 'GET':
                req = requests.get(request_url, headers=req_headers)

            if request_method == 'POST':
                req = requests.post(request_url, json=request_body, headers=req_headers)
        except:
            pass
        client.close()
        return jsonify({"Message":"Success"})
    except:
        return jsonify({"Message":"Failure"})

@app.route('/calls/voicemail', methods=['POST'])
def updateVoicemail():
    try:
        client = pymongo.MongoClient("mongodb+srv://admin:QM6icvpQ6SlOveul@cluster0.vc0rw.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        mongoDB = client['jamesbon']
        post_data = request.json
        logger.debug('Interest Data: {}'.format(str(request.json)))
        leads_col = mongoDB['leads']

        # Update Lead as interested
        search_query = {
            "call_logs.call_id":post_data['CallSid']
        }
        update_query = {
            '$set':{
                'status':'voicemail',
                'updated_at':str(datetime.datetime.utcnow())[:-7]
            }
        }
        leads_col.update_one(search_query,update_query)
        return jsonify({"Message":"Success"})
    except:
        return jsonify({"Message":"Failure"})

@app.route('/calls/hangup/<call_sid>', methods=['GET', 'POST'])
def callHangup(call_sid):
    try:
        logger.debug('Hangup Data')
        client = pymongo.MongoClient("mongodb+srv://admin:QM6icvpQ6SlOveul@cluster0.vc0rw.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        mongoDB = client['jamesbon']
        leads_col = mongoDB['leads']
        search_query = {
            "call_logs.call_id":call_sid
        }
        lead = leads_col.find_one(search_query)
        campaigns_col = mongoDB['campaigns']
        campaign = campaigns_col.find_one({'_id':lead['campaign_id']})

        logger.debug('\t Stop recording')
        companies_col = mongoDB['companies']
        company = companies_col.find_one({'_id':campaign['company_id']})
        try:
            try:
                twilio_account_sid = company['twilio_account_sid']
                logger.debug('\t\t Account SID: {}'.format(twilio_account_sid))
            except:
                logger.error('\t\t Failed Grabbing Account SID')
            try:
                twilio_auth_token = company['twilio_auth_token']
                logger.debug('\t\t Auth Token: {}'.format(twilio_auth_token))
            except:
                logger.error('\t\t Failed Grabbing Auth Token')
            try:
                twil_client = Client(twilio_account_sid, twilio_auth_token)
                logger.debug('\t\t Created Twil Client')
            except:
                logger.error('\t\t Failed Creating Twil Client')
            try:
                logger.debug('\t\t Find Recording Using: {}'.format(str(call_sid)))
                recording = twil_client.calls(str(call_sid)).recordings.list(limit=1)
                try:
                    logger.debug('\t\t Find Total Of {} Recordings'.format(str(len(recording))))
                except:
                    pass
                recording_id = str(recording[0].sid)
                logger.debug('\t\t Recording ID: {}'.format(recording_id))
            except:
                logger.error('\t\t Failed Grabbing Recording ID')
            try:
                twil_client.calls(str(call_sid)).recordings(recording_id).update(status='stopped')
                logger.debug('\t Stop Record Successful')
            except:
                logger.error('\t\t Failed Sending Stop Request')
        except:
            logger.error('\t Failed to stop recording')
        client.close()
        return jsonify({"Message":"Success"})
    except:
        return jsonify({"Message":"Failure"})

@app.route('/calls/dnc', methods=['POST'])
def updateLeadDNC():
    try:
        client = pymongo.MongoClient("mongodb+srv://admin:QM6icvpQ6SlOveul@cluster0.vc0rw.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        mongoDB = client['jamesbon']
        post_data = request.json
        logger.debug('Interest Data: {}'.format(str(request.json)))
        leads_col = mongoDB['leads']

        # Update Lead as Do Not Call
        search_query = {
            "call_logs.call_id":post_data['CallSid']
        }
        update_query = {
            '$set':{
                'dnc':True,
                'updated_at':str(datetime.datetime.utcnow())[:-7]
            }
        }
        leads_col.update_one(search_query,update_query)
        return jsonify({"Message":"Success"})
    except:
        return jsonify({"Message":"Failure"})

@app.route('/calls/dial_call_back', methods=['POST'])
def callDialBack():
    try:
        print(str(request.form))
        logger.debug('DIAL BACK DATA: {}'.format(str(request.form)))
    except:
        print(str(request.json))
        logger.debug('DIAL BACK DATA: {}'.format(str(request.json)))
    return jsonify({'Message':'Success'})

@app.route('/calls/xfer_number/<token>', methods=['GET'])
def getTransferNumber(token):
    try:
        client = pymongo.MongoClient("mongodb+srv://admin:QM6icvpQ6SlOveul@cluster0.vc0rw.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        mongoDB = client['jamesbon']
        virtual_col = mongoDB['virtual_agents']
        filter_by = {
            '_id':ObjectId(token)
        }
        virtual_admin = virtual_col.find_one(filter_by)
        if virtual_admin:
            return jsonify({'number':virtual_admin['xfer']})
        client.close()
    except:
        pass
    return jsonify({'number':'Failure'})

@app.route('/calls/dial_tone', methods=['POST'])
def callDialTone():
    try:
        print(str(request.form))
        logger.debug('DIAL TONE DATA: {}'.format(str(request.form)))
    except:
        print(str(request.json))
        logger.debug('DIAL TONE DATA: {}'.format(str(request.json)))
    return jsonify({'Message':'Success'})

def getDecimal(x):
    try:
        #return Decimal(x.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
        return float(x)
    except:
        x = 0
        #return Decimal(x.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
        return float(x)

def getInt(x):
    try:
        #return Decimal(x.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
        return int(x)
    except:
        x = 0
        #return Decimal(x.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
        return int(x)

def simpleUpdateRow(collection, data, post_type):
    if post_type == 'POST':
        try:
            if isinstance(data, list):
                for x in data:
                    for key in x:
                        if '_id' in key:
                            try:
                                x[key] = ObjectId(x[key])
                            except:
                                x[key] = x[key]
                        else:
                            x[key] = x[key]
                    x['created_at'] = str(datetime.datetime.utcnow())[:-3]
                    x['updated_at'] = str(datetime.datetime.utcnow())[:-3]
                    _id = collection.insert(x)
            else:
                for key in data:
                    if '_id' in key:
                        try:
                            data[key] = ObjectId(data[key])
                        except:
                            data[key] = data[key]
                data['created_at'] = str(datetime.datetime.utcnow())[:-3]
                data['updated_at'] = str(datetime.datetime.utcnow())[:-3]
                _id = collection.insert(data)
            return {
                'Message':'Success',
                'id':str(_id)
            }
        except:
            return {'Message':'Failure'}
    elif post_type == 'PUT':
        try:
            data['updated_at'] = str(datetime.datetime.utcnow())[:-3]
            updateQuery = {
                "$set":{
                    'updated_at':str(datetime.datetime.utcnow())[:-7]
                }
            }
            for key in data:
                if '_id' in key:
                    try:
                        updateQuery["$set"][key]  = ObjectId(data[key])
                    except:
                        updateQuery["$set"][key]  = data[key]
                elif key != 'id':
                    updateQuery["$set"][key] = data[key]
                else:
                    updateQuery["$set"][key] = data[key]
            search_query = {
                "_id":ObjectId(data['id'])
            }
            collection.update_one(search_query, updateQuery)
            return {
                'Message':'Success',
                'id':data['id']
            }
        except:
            return {'Message':'Failure'}
    elif post_type == 'DELETE':
        try:
            collection.delete_one({"_id":ObjectId(data['id'])})
            return {
                'Message':'Success',
                'id':data['id']
            }
        except:
            return {'Message':'Failure'}
    return {'Message':'Failure'}

def convertToJSON(obj):
    objData = {}
    for key in obj:
        if key != 'password':
            if isinstance(obj[key], list):
                objData[key] = []
                thisList = []
                for x in range(0, len(obj[key])):
                    thisDict = {}
                    for listKey in obj[key][x]:
                        if isinstance(obj[key][x][listKey], str):
                            thisDict[listKey] = str(obj[key][x][listKey])
                        elif isinstance(obj[key][x][listKey], bytes):
                            thisDict[listKey] = str(obj[key][x][listKey])
                        elif isinstance(obj[key][x][listKey], bool):
                            thisDict[listKey] = obj[key][x][listKey]
                        elif isinstance(obj[key][x][listKey], int):
                            thisDict[listKey] = getInt(obj[key][x][listKey])
                        elif isinstance(obj[key][x][listKey], float):
                            thisDict[listKey] = getDecimal(obj[key][x][listKey])
                        elif isinstance(obj[key][x][listKey], ObjectId):
                            thisDict[listKey] = str(obj[key][x][listKey])
                        else:
                            thisDict[listKey] = obj[key][x][listKey]
                    thisList.append(thisDict)
                
                objData[key] = thisList

            else:
                if isinstance(obj[key], str):
                    objData[key] = str(obj[key])
                elif isinstance(obj[key], bytes):
                    objData[key] = str(obj[key])
                elif isinstance(obj[key], bool):
                    objData[key] = obj[key]
                elif isinstance(obj[key], int):
                    objData[key] = getInt(obj[key])
                elif isinstance(obj[key], float):
                    objData[key] = getDecimal(obj[key])
                elif isinstance(obj[key], ObjectId):
                    objData[key] = str(obj[key])
                else:
                    objData[key] = obj[key]
    try:
        objData['id'] = objData['_id']
        objData.pop('_id')
    except:
        pass
    return objData

def delimiterReplace(str_full, data):
    curr_first = -1
    indices = []
    for indx, char in enumerate(str_full):
        if char == '[':
            curr_first = indx
        elif char == ']' and curr_first != -1:
            indices.append([curr_first, indx])
            curr_first = -1

    first_index = indices[0][0]
    first_part = str_full[0:first_index]
    full_str = first_part
    last_index = 0
    for indx, indice in enumerate(indices):
        first_index = indice[0]
        last_index = indice[1]
        mid_part = str_full[first_index+1:last_index]
        last_index
        try:
            value = data[mid_part]
        except:
            value = str_full[first_index:last_index+1]
        try:
            next_part = str_full[last_index+1:indices[indx+1][0]]
        except:
            next_part = ''
        full_str += value+next_part

    last_part = str_full[last_index+1:len(str_full)]
    full_str += last_part
    return full_str