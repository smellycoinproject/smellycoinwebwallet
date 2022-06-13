import flask
from flask import Flask 
from flask import Flask, session, redirect, url_for, escape, request, render_template
import requests
import json
from flask import flash
from flask import Markup
import traceback
from wtforms.validators import ValidationError, DataRequired
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import os



app = Flask(__name__)

app.secret_key = os.urandom(150)


rpcurl = "http://127.0.0.1:3001"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/wallet')
def wallet_page():
    try:
        if session['addressid'] == "":
            return redirect(url_for('login'))
        if session['password'] == "":
            return redirect(url_for('login'))
        if session['addressid'] == None:
            return redirect(url_for('login'))
        if session['password'] == None:
            return redirect(url_for('login'))
    except KeyError:
        return redirect(url_for('login')) 
    """
    return f'''
    your addrid = {session["addressid"]}
    your password = {session["password"]}
    '''
    """
    balanced = requests.get(f"{rpcurl}/operator/{session['walletaddress']}/balance")
    output = balanced.content
    try:
        #print(output)
        json_data = json.loads(output)
        json_data = json.loads(output)
        if "balance" in json_data:
            balance = json_data["balance"]
    except:
        #print(output)
        balance = float(0.0)
    return render_template('wallet.html', balance=balance, addressid=session['walletaddress'])


@app.route('/login', methods = ['GET', 'POST'])
def login():
    '''
    let walletId = req.body["walletId"]
    let password = req.body["password"]
    '''
    if request.method == 'POST':
        session["addressid"] = request.form["addressid"]
        session['password'] = request.form["password"]
        addrc = requests.get(f'{rpcurl}/operator/wallets/{request.form["addressid"]}/addresses')
        try:
            addresses = eval(requests.get(f'{rpcurl}/operator/wallets/{request.form["addressid"]}/addresses').text)
        except:
            flash(f'<script>alert("Wallet Not Found in web wallet database with wallet ID: {request.form["addressid"]}");</script>', 'error')
            return redirect(url_for('login'))

        #print(len(addresses))
        if len(addresses) < 1:
            headr = {"password": request.form["password"]}
            op = requests.post(f"{rpcurl}/operator/wallets/{request.form['addressid']}/addresses", headers=headr)
            newop = requests.get(f'{rpcurl}/operator/wallets/{request.form["addressid"]}/addresses').text
            #print('newop '+newop)
            session['walletaddress'] = eval(newop)[0]
            print(newop)
            print(newop[0])
            #print('newop[0] '+newop[0])
        else:
            session['walletaddress'] = addresses[0]
            #print(f"\033[01;32maddr0: {addresses[0]}\033[00m")
        #print(addresses)
        logindat = {
            "walletId": request.form["addressid"],
            "password": request.form["password"],
        }
        validity = requests.post(f'{rpcurl}/operator/wallet/verify', json=logindat)
        print(validity.response_code)
        if validity.text == "True":
            #print('True')
            flash('<script>alert("Login Successful!");</script>', 'succsess')
            return redirect(url_for('wallet_page'))
        else:
            #print(request.form["addressid"])
            #print(request.form["password"])
            #print(validity)
            #print(validity.text)
            session.pop('addressid', None)
            session.pop('privatekey', None)
            flash('<script>alert("Incorrect Address ID or password!");</script>', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/wallet/transactions/new', methods=["GET", "POST"])
def transactionspage():
    try:
        if session['addressid'] == "":
            return redirect(url_for('login'))
        if session['password'] == "":
            return redirect(url_for('login'))
        if session['addressid'] == None:
            return redirect(url_for('login'))
        if session['password'] == None:
            return redirect(url_for('login'))
    except KeyError:
        return redirect(url_for('login')) 
    if request.method == 'POST':
        to = request.form['recv']
        try:
            amount = float(request.form['amount'])
        except ValueError:
            flash(Markup('<script>alert("Missing Amount To Send!");</script>'), 'error')
            return redirect(url_for('transactionspage'))
        dat = {
            "fromAddress": session['walletaddress'],
            "toAddress": to,
            "amount": float(amount),
            "changeAddress": session['walletaddress']
        }
        headr = {"password": session['password']}
        try:
            tx = requests.post(f'{rpcurl}/operator/wallets/{session["addressid"]}/transactions', headers=headr, json=dat)
            print(tx)
            print(tx.content)
            if tx.status_code == 400:
                flash(Markup('<script>alert("Insufficent Balance to send transaction check amount entered and account for atleast 0.000001 smellycoin fee.");</script>'), 'error')
                redirect(url_for('transactionspage'))
            elif tx.status_code == 201:
                txc = tx.content
                json_data = json.loads(txc)
                flash(Markup(f'<script>alert("Success Sending Transaction! TXID: {json_data["id"]}");</script>'), 'success')
                redirect(url_for('transactionspage'))
            else:
                flask(Markup('<script>alert("Error Sending Transaction");</script>'))
                redirect(url_for('transactionspage'))
        except Exception as e:
            print(traceback.format_exc())
    balanced = requests.get(f"{rpcurl}/operator/{session['walletaddress']}/balance")
    output = balanced.content
    try:
        #print(output)
        json_data = json.loads(output)
        json_data = json.loads(output)
        if "balance" in json_data:
            balance = json_data["balance"]
    except:
        #print(output)
        balance = float(0.0)
    return render_template('transaction.html', balance=balance)


@app.route('/faq', methods=["GET"])
def faq():
    return render_template('faq.html')



@app.route('/logout')
def logout():
   # remove the username from the session if it is there
   session.pop('addressid', None)
   session.pop('privatekey', None)
   session.pop('walletaddress', None)
   session.clear()
   return redirect(url_for('login'))





app.run(host="0.0.0.0", port=8080)