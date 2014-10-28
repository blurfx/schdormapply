# -*- coding: utf-8 -*-
import requests, re, logging
import xml.etree.ElementTree as ET
from flask import Flask,render_template,request,redirect,session,escape,make_response
from requests.adapters import HTTPAdapter
from datetime import timedelta,datetime

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

app = Flask(__name__,static_url_path='',static_folder ='static/')
app.secret_key = 'lUN4T1k=07/90D!or,G0D?oF/L6N4t1CCCCC'

app.permanent_session_lifetime = timedelta(minutes=5)

requests.adapters.DEFAULT_RETRIES = 10

loginHost = 'http://st.sch.ac.kr/web/cpj/login.xpl'
portalHost = 'http://st.sch.ac.kr/web/tpj/standard.xpl'
portalHeader = {'Content-Type': 'application/xml'}

r = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=10)
r.mount(portalHost,adapter)

loginFailure = 0
submitFailure = False
submitData = {}

@app.route('/')
def index():

    if 'stdId' in session:
        return redirect('/list')
    else:
        global loginFailure

    if request.cookies.get('storeId'):
        userid = request.cookies.get('storeId')
    else:
        userid = None

    render = render_template('login.html',error=loginFailure,uid=userid)
    loginFailure = None

    logging.warn(('{0}\t{1}').format(re.sub(r'(\d{1,3})?.(\d{1,3})$','*.*',request.remote_addr),'/'))
    return render

@app.route('/logout')
def logout():
    session.clear()

    logging.warn(('{0}\t{1}').format(re.sub(r'(\d{1,3})?.(\d{1,3})$','*.*',request.remote_addr),'/logout'))
    return redirect('/')

@app.route('/login',methods=['POST'])
def login():

    global loginFailure

    #get smt from
    data = "<?xml version='1.0' encoding='UTF-8' ?><Root><Parameters><Parameter id=\"SCHLBSWITCH\" type=\"STRING\">FBLNEFNM</Parameter><Parameter id=\"JSESSIONID\" type=\"STRING\">FAKESESS</Parameter><Parameter id=\"HttpOnly\" type=\"STRING\"></Parameter><Parameter id=\"ncTrId\" type=\"STRING\">TDMBASE_pSearchBaseYear</Parameter></Parameters></Root>"

    s = r.post(portalHost,data=data,headers=portalHeader)
    smt = re.findall(r"<Col id=\"SMT\">(\d*)</Col>",s.text)

    data = "<?xml version='1.0' encoding='UTF-8' ?><Root><Parameters><Parameter id=\"SCHLBSWITCH\" type=\"STRING\">FBLNEFNM</Parameter><Parameter id=\"JSESSIONID\" type=\"STRING\">FAKESESS</Parameter><Parameter id=\"HttpOnly\" type=\"STRING\"></Parameter><Parameter id=\"ncTrId\" type=\"STRING\">TDMSLEP_pSearchSleepOutAply</Parameter></Parameters><Dataset id=\"ncFieldMap\"><ColumnInfo><Column id=\"STD_NO\" type=\"STRING\" size=\"256\"></Column><Column id=\"YY\" type=\"STRING\" size=\"256\"></Column><Column id=\"SMT\" type=\"STRING\" size=\"256\"></Column></ColumnInfo><Rows><Row><Col id=\"STD_NO\">" + request.form['id'] + "</Col><Col id=\"YY\">" + str(datetime.now().year) + "</Col><Col id=\"SMT\">"+ smt[0] + "</Col></Row></Rows></Dataset></Root>"
    s = r.post(portalHost,data=data,headers=portalHeader)
    #print(s.text)

    info = re.findall(r"<Col id=\"(\S*)\">(\S*)</Col>",s.text)

    for key in info:
        session[key[0]] = key[1]

    if(len(session) < 4):
        session.clear()
        global loginFailure
        loginFailure = 3
        return redirect('/')

    data = "<?xml version=\"1.0\" encoding=\"utf-8\"?><Root><Parameters><Parameter id=\"SCHLBSWITCH\" type=\"STRING\">FBLNEFNM</Parameter>" \
"</Parameters><Dataset id=\"ncFieldMap\"><ColumnInfo><Column id=\"EMP_STD_NO\" type=\"STRING\" size=\"256\"/>" \
"<Column id=\"PASSWD\" type=\"STRING\" size=\"256\"/><Column id=\"USER_DIV_CD\" type=\"STRING\" size=\"256\"/></ColumnInfo>" \
"<Rows><Row><Col id=\"EMP_STD_NO\">" + request.form['id'] + "</Col><Col id=\"PASSWD\">" + request.form['pw'] + "</Col><Col id=\"USER_DIV_CD\">C0080003</Col></Row></Rows></Dataset></Root>"

    s = r.post(loginHost,data=data,headers=portalHeader)
    code = re.findall(r"(MSGI\d{4})",s.text)



    if (code[0] == 'MSGI0006'):

        session['NM_ENG'] = re.findall(r"<Col id=\"ENG_NM\">(\S*)</Col>",s.text)[0]

        loginFailure = 0

        session.permanent = True
        session['stdId'] = request.form['id']

        response = make_response(redirect('/list'))

        if request.form.get('storeId'):
            response.set_cookie('storeId',session['stdId'])
        else:
            response.set_cookie('storeId','')
        logging.warn(('{0}\t{1} {2}').format(re.sub(r'(\d{1,3})?.(\d{1,3})$','*.*',request.remote_addr),'/login', 'success'))
        return response

    elif(code[0] == "MSGI0005"):
        loginFailure = 1
        logging.warn(('{0}\t{1} {2}').format(re.sub(r'(\d{1,3})?.(\d{1,3})$','*.*',request.remote_addr),'/login','wrong pw'))
        return redirect('/')

    else:
        loginFailure = 2
        logging.warn(('{0}\t{1} {2}').format(re.sub(r'(\d{1,3})?.(\d{1,3})$','*.*',request.remote_addr),'/login','no such id'))
        return redirect('/')


@app.route('/list', methods=['POST','GET'])
def list():

    if not 'stdId' in session:
        return redirect('/')

    yesterday = datetime.today() - timedelta(1)
    tomorrow = datetime.today() + timedelta(1)

    data = "<?xml version='1.0' encoding='UTF-8' ?><Root><Parameters><Parameter id=\"SCHLBSWITCH\" type=\"STRING\">FBLNEFNM</Parameter>" \
           "<Parameter id=\"JSESSIONID\" type=\"STRING\">FAKESESS</Parameter><Parameter id=\"HttpOnly\" type=\"STRING\"></Parameter>" \
           "<Parameter id=\"ncTrId\" type=\"STRING\">TDMSLEP_pSearchSleepOut</Parameter></Parameters><Dataset id=\"ncFieldMap\">" \
           "<ColumnInfo><Column id=\"SLEEP_OUT_FR_DT\" type=\"STRING\" size=\"256\"></Column>" \
           "<Column id=\"SLEEP_OUT_TO_DT\" type=\"STRING\" size=\"256\"></Column><Column id=\"BLD_CD\" type=\"STRING\" size=\"256\">" \
           "</Column><Column id=\"NM\" type=\"STRING\" size=\"256\"></Column><Column id=\"SLEEP_OUT_RSN\" type=\"STRING\" size=\"256\">" \
           "</Column><Column id=\"APRV_YN\" type=\"STRING\" size=\"256\"></Column><Column id=\"STD_NO\" type=\"STRING\" size=\"256\">" \
           "</Column></ColumnInfo><Rows><Row>" \
           "<Col id=\"SLEEP_OUT_FR_DT\">" + yesterday.strftime('%Y%m%d') + "</Col>" \
           "<Col id=\"SLEEP_OUT_TO_DT\">" + tomorrow.strftime('%Y%m%d') +  "</Col>" \
           "<Col id=\"STD_NO\">" + session['stdId'] + "</Col></Row><Row></Row><Row></Row><Row></Row><Row></Row><Row></Row><Row></Row></Rows></Dataset></Root>"

    s = r.post(portalHost,data=data,headers=portalHeader)
    root = ET.fromstring(s.text)

    applyList = []
    applies = {}

    #get list
    for child in root[1][1]:
        applies = {}
        for sub in child:
            applies[sub.attrib['id']] = sub.text
            #print sub.attrib['id'], sub.text
        applyList.append(applies)
    session['applyList'] = applyList

    reasons = {1: '귀가',2:'과제',3:'MT',4:'졸업여행',5:'졸업작품 준비',6:'기타'}

    for i in range(0,len(applyList)):
        applyList[i]['SLEEP_OUT_RSN_EDIT'] = reasons[int(applyList[i]['SLEEP_OUT_RSN'][-1])]
        applyList[i]['SLEEP_OUT_DT_EDIT'] = datetime.strptime(applyList[i]['SLEEP_OUT_DT'],'%Y%m%d').strftime('%m/%d')

    logging.warn(('{0}\t{1}').format(re.sub(r'(\d{1,3})?.(\d{1,3})$','*.*',request.remote_addr),'/list'))
    return render_template('list.html',list=applyList)

@app.route('/delete',methods=['POST'])
def delete():

    if not 'stdId' in session:
        return redirect('/')

    index = int(request.form.get('index'))
    index -= 1

    #for key in session['applyList'][index]:
    #    print key, session['applyList'][index][key]


    data = "<?xml version='1.0' encoding='UTF-8' ?><Root><Parameters><Parameter id=\"SCHLBSWITCH\" type=\"STRING\">FBLNEFNM</Parameter>" \
           "<Parameter id=\"JSESSIONID\" type=\"STRING\">FAKESESSS</Parameter><Parameter id=\"HttpOnly\" type=\"STRING\">" \
           "</Parameter><Parameter id=\"ncTrId\" type=\"STRING\">TDMSLEP_pSaveSleepOutAply</Parameter></Parameters>" \
           "<Dataset id=\"RS_SLEP_OUT_SAVE\"><ColumnInfo><Column id=\"EMERGEN_CONTACT\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"YY\" type=\"STRING\" size=\"255\"></Column><Column id=\"NM_ENG\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"DEST\" type=\"STRING\" size=\"255\"></Column><Column id=\"REMARK\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"SHYR\" type=\"STRING\" size=\"255\"></Column><Column id=\"APLY_DIV\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"MJ_CD\" type=\"STRING\" size=\"55\"></Column><Column id=\"GRADS\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"STD_NO\" type=\"STRING\" size=\"255\"></Column><Column id=\"SUST_CD\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"CHK\" type=\"STRING\" size=\"255\"></Column><Column id=\"GRADS_CORS_CD\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"SEX\" type=\"STRING\" size=\"255\"></Column><Column id=\"SUST_NM\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"DTLS_ROOM\" type=\"STRING\" size=\"255\"></Column><Column id=\"NM_KRN\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"ORGN_DIV\" type=\"STRING\" size=\"255\"></Column><Column id=\"APPVR_NM\" type=\"STRING\" size=\"55\">" \
           "</Column><Column id=\"SSN\" type=\"STRING\" size=\"55\"></Column><Column id=\"UNIV_NM\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"ROOM_NO\" type=\"STRING\" size=\"255\"></Column><Column id=\"APLY_DT\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"UP_DW_DIV_NM\" type=\"STRING\" size=\"255\"></Column><Column id=\"BLD_NM\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"UP_DW_DIV\" type=\"STRING\" size=\"255\"></Column><Column id=\"NM_CHI\" type=\"STRING\" size=\"55\">" \
           "</Column><Column id=\"MJ_NM\" type=\"STRING\" size=\"55\"></Column><Column id=\"SLEEP_OUT_DT\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"SLEEP_OUT_RSN\" type=\"STRING\" size=\"255\"></Column><Column id=\"PRSNL_NO\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"APRV_YN\" type=\"STRING\" size=\"55\"></Column><Column id=\"BLD\" type=\"STRING\" size=\"255\">" \
           "</Column><Column id=\"SMT\" type=\"STRING\" size=\"255\"></Column></ColumnInfo><Rows><Row type=\"delete\">" \
           "<Col id=\"EMERGEN_CONTACT\">" + (session['applyList'][index]['EMERGEN_CONTACT'] or '') + "</Col>" \
           "<Col id=\"YY\">" + session['applyList'][index]['YY'] + "</Col>" \
           "<Col id=\"NM_ENG\">" + session['NM_ENG'] + "</Col>" \
           "<Col id=\"DEST\">" + (session['applyList'][index]['DEST'] or '') + "</Col>" \
           "<Col id=\"REMARK\">" + (session['applyList'][index]['REMARK'] or '') + "</Col>" \
           "<Col id=\"SHYR\">" + session['applyList'][index]['SHYR'] + "</Col>" \
           "<Col id=\"APLY_DIV\">" + session['applyList'][index]['APLY_DIV'] + "</Col>" \
           "<Col id=\"MJ_CD\"></Col>" \
           "<Col id=\"GRADS\">" + session['applyList'][index]['GRADS'] + "</Col>" \
           "<Col id=\"STD_NO\">" + session['applyList'][index]['STD_NO'] + "</Col>" \
           "<Col id=\"SUST_CD\">" + session['applyList'][index]['SUST_CD'] + "</Col>" \
           "<Col id=\"CHK\">" + session['applyList'][index]['CHK'] + "</Col>" \
           "<Col id=\"GRADS_CORS_CD\">" + session['applyList'][index]['GRADS_CORS_CD'] + "</Col>" \
           "<Col id=\"SEX\">" + session['applyList'][index]['SEX'] + "</Col>" \
           "<Col id=\"SUST_NM\"></Col>" \
           "<Col id=\"DTLS_ROOM\">" + session['applyList'][index]['DTLS_ROOM'] + "</Col>" \
           "<Col id=\"NM_KRN\"></Col>" \
           "<Col id=\"ORGN_DIV\">" + session['applyList'][index]['ORGN_DIV'] + "</Col>" \
           "<Col id=\"APPVR_NM\"></Col>" \
           "<Col id=\"SSN\"></Col>" \
           "<Col id=\"UNIV_NM\"></Col>" \
           "<Col id=\"ROOM_NO\">" + session['applyList'][index]['ROOM_NO'] + "</Col>" \
           "<Col id=\"APLY_DT\">" + session['applyList'][index]['APLY_DT'] + "</Col>" \
           "<Col id=\"UP_DW_DIV_NM\"></Col>" \
           "<Col id=\"BLD_NM\">" + escape(session['applyList'][index]['BLD_NM']).encode('ascii','ignore')  + "</Col>" \
           "<Col id=\"UP_DW_DIV\">" + session['applyList'][index]['UP_DW_DIV'] + "</Col>" \
           "<Col id=\"NM_CHI\"></Col>" \
           "<Col id=\"MJ_NM\"></Col>" \
           "<Col id=\"SLEEP_OUT_DT\">" + session['applyList'][index]['SLEEP_OUT_DT'] + "</Col>" \
           "<Col id=\"SLEEP_OUT_RSN\">" + session['applyList'][index]['SLEEP_OUT_RSN'] + "</Col>" \
           "<Col id=\"PRSNL_NO\">" + session['applyList'][index]['PRSNL_NO'] + "</Col>" \
           "<Col id=\"APRV_YN\"></Col>" \
           "<Col id=\"BLD\">" + session['applyList'][index]['BLD'] + "</Col>" \
           "<Col id=\"SMT\">" + session['applyList'][index]['SMT'] + "</Col>" \
           "</Row></Rows></Dataset></Root>"
    print data
    s = r.post(portalHost,data=data.encode('utf8'),headers=portalHeader)
    logging.warn(('{0}\t{1}').format(re.sub(r'(\d{1,3})?.(\d{1,3})$','*.*',request.remote_addr),'/delete'))
    return redirect('/list')

#TDMSLEP_pSaveSleepOutAply 20141016235223027 20141016235223041 MSGI0002 저장이 완료되었습니다. OK 0 OK

@app.route('/apply', methods=['POST','GET'])
def apply():

    #check user is signed in
    if not 'stdId' in session:
        return redirect('/')

    #check is trying rewrite by submit failure
    global submitFailure

    if(submitFailure):
        return render_template('apply.html',contact=session['EMERGEN_CONTACT'],error=True)

    logging.warn(('{0}\t{1}').format(re.sub(r'(\d{1,3})?.(\d{1,3})$','*.*',request.remote_addr),'/apply'))
    return render_template('apply.html',contact=session['EMERGEN_CONTACT'])



@app.route('/submit',methods=['POST'])
def submit():

    if not 'stdId' in session:
        return redirect('/')

    data = "<?xml version=\"1.0\" encoding=\"utf-8\"?><Root><Parameters><Parameter id=\"SCHLBSWITCH\" type=\"STRING\">FCLNEFNM</Parameter>" \
           "<Parameter id=\"JSESSIONID\" type=\"STRING\">FAKESSES</Parameter>" \
           "<Parameter id=\"HttpOnly\" type=\"STRING\"></Parameter>" \
           "<Parameter id=\"ncTrId\" type=\"STRING\">TDMSLEP_pSaveSleepOutAply</Parameter></Parameters>" \
           "<Dataset id=\"RS_SLEP_OUT_SAVE\"> <ColumnInfo> <Column id=\"EMERGEN_CONTACT\" type=\"STRING\" size=\"255\"/>" \
           "<Column id=\"YY\" type=\"STRING\" size=\"255\"/> <Column id=\"DEST\" type=\"STRING\" size=\"55\"/>" \
           "<Column id=\"SHYR\" type=\"STRING\" size=\"255\"/> <Column id=\"REMARK\" type=\"STRING\" size=\"55\"/>" \
           "<Column id=\"APLY_DIV\" type=\"STRING\" size=\"255\"/> <Column id=\"GRADS_NM\" type=\"STRING\" size=\"255\"/>" \
           "<Column id=\"ORGN_DIV_NM\" type=\"STRING\" size=\"255\"/> <Column id=\"APLY_TM_YN\" type=\"STRING\" size=\"255\"/>" \
           "<Column id=\"STD_NO\" type=\"STRING\" size=\"255\"/> <Column id=\"CORS_NM\" type=\"STRING\" size=\"55\"/>" \
           "<Column id=\"SEX\" type=\"STRING\" size=\"255\"/> <Column id=\"SUST_NM\" type=\"STRING\" size=\"255\"/>" \
           "<Column id=\"DTLS_ROOM\" type=\"STRING\" size=\"255\"/> <Column id=\"ORGN_DIV\" type=\"STRING\" size=\"255\"/>" \
           "<Column id=\"APPVR_NM\" type=\"STRING\" size=\"55\"/> <Column id=\"APLY_DT\" type=\"STRING\" size=\"55\"/>" \
           "<Column id=\"ROOM_NO\" type=\"STRING\" size=\"255\"/> <Column id=\"BLD_NM\" type=\"STRING\" size=\"255\"/>" \
           "<Column id=\"MJ_NM\" type=\"STRING\" size=\"55\"/> <Column id=\"SLEEP_OUT_DT\" type=\"STRING\" size=\"55\"/>" \
           "<Column id=\"NM\" type=\"STRING\" size=\"255\"/> <Column id=\"SLEEP_OUT_RSN\" type=\"STRING\" size=\"55\"/>" \
           "<Column id=\"PRSNL_NO\" type=\"STRING\" size=\"255\"/> <Column id=\"APRV_YN\" type=\"STRING\" size=\"55\"/>" \
           "<Column id=\"BLD\" type=\"STRING\" size=\"255\"/> <Column id=\"SMT\" type=\"STRING\" size=\"255\"/>" \
           "<Column id=\"REG_USER_NO\" type=\"STRING\" size=\"256\"/> <Column id=\"MOD_USER_NO\" type=\"STRING\" size=\"256\"/></ColumnInfo>" \
           "<Rows> <Row type=\"insert\">" \
           "<Col id=\"EMERGEN_CONTACT\">" + request.form['emer'] + "</Col>" \
           "<Col id=\"YY\">" + session['YY'] + "</Col>" \
           "<Col id=\"DEST\">" + request.form['dest'] +"</Col>" \
           "<Col id=\"SHYR\">" + session['SHYR'] + "</Col>" \
           "<Col id=\"REMARK\">" + request.form['cmnt'] + "</Col>" \
           "<Col id=\"APLY_DIV\">" + session['APLY_DIV'] + "</Col>" \
           "<Col id=\"GRADS_NM\"></Col>" \
           "<Col id=\"ORGN_DIV_NM\"></Col>" \
           "<Col id=\"APLY_TM_YN\">Y</Col>" \
           "<Col id=\"STD_NO\">" + session['stdId'] + "</Col>" \
           "<Col id=\"CORS_NM\"/>" \
           "<Col id=\"SEX\">" + session['SEX'] + "</Col>" \
           "<Col id=\"SUST_NM\"></Col>" \
           "<Col id=\"DTLS_ROOM\">" + session['DTLS_ROOM'] + "</Col>" \
           "<Col id=\"ORGN_DIV\">" + session['ORGN_DIV'] + "</Col>" \
           "<Col id=\"APPVR_NM\"/>" \
           "<Col id=\"APLY_DT\"/>" \
           "<Col id=\"ROOM_NO\">" + session['ROOM_NO'] + "</Col>" \
           "<Col id=\"BLD_NM\">" + escape(session['BLD_NM']).encode('ascii','ignore') + "</Col>" \
           "<Col id=\"MJ_NM\"/>" \
           "<Col id=\"SLEEP_OUT_DT\">" + re.sub(r"[^0-9]",'',request.form['date']) + "</Col>" \
           "<Col id=\"NM\"></Col>" \
           "<Col id=\"SLEEP_OUT_RSN\">T129000"+ str(int(request.form['resn'])) + "</Col>" \
           "<Col id=\"PRSNL_NO\">" + session['stdId'] + "</Col>" \
           "<Col id=\"APRV_YN\"/>" \
           "<Col id=\"BLD\">" + session['BLD'] + "</Col>" \
           "<Col id=\"SMT\">" + session['SMT'] + "</Col>" \
           "<Col id=\"REG_USER_NO\">H" + str(session['stdId']) + "</Col>" \
           "<Col id=\"MOD_USER_NO\">H" + str(session['stdId']) + "</Col>" \
           "</Row></Rows></Dataset></Root>"

    reqData = request.form

    s = r.post(portalHost,data=data.encode('utf8'),headers=portalHeader)

    global submitFailure
    global submitData

    submitData = request.form

    if('MSGI0002' in s.text):
        logging.warn(('{0}\t{1} {2}').format(re.sub(r'(\d{1,3})?.(\d{1,3})$','*.*',request.remote_addr),'/submit','success'))
        submitFailure = False
        return redirect('/result')
    else:
        submitFailure = True
        logging.warn(('{0}\t{1} {2}').format(re.sub(r'(\d{1,3})?.(\d{1,3})$','*.*',request.remote_addr),'/submit','fail'))
        return redirect('/apply')


@app.route('/result',methods=['POST','GET'])
def result():

    global submitData

    if not 'stdId' in session or submitData is None:
        return redirect('/')

    reasons = {1: '귀가',2:'과제',3:'MT',4:'졸업여행',5:'졸업작품 준비',6:'기타'}
    reasonStr = reasons [int(submitData['resn'])]

    render = render_template('result.html',data=submitData,reasonStr=reasonStr)
    logging.warn(('{0}\t{1}').format(re.sub(r'(\d{1,3})?.(\d{1,3})$','*.*',request.remote_addr),'/result'))
    return render

#TDMSLEP_pSaveSleepOutAply 20140927010811956 20140927010811969 MSGI0002 저장이 완료되었습니다. OK 0 OK
#TDMSLEP_pSaveSleepOutAply 20140927011905587 20140927011905604 Unknown[ : ko_KR] ERROR -1 ERROR

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S',
                    filename='/Users/DevBird/schlog/'+datetime.today().strftime('%y%m%d')+'.log',
                    filemode='w')
    app.run(host='0.0.0.0',port=88,debug=True)

