//var DEF_HOST = "../../api"
var DEF_HOST = ""
var TEMPLATE_POST = {method: 'POST',headers: {'Content-Type': 'application/json',},}
var host = ""
var qr_inner = {}

hosthandle(false)
login(false)
register(false)
logout(false)
unregister(false)
userinfo(false)
test(false)
hostez()

function qrmadein(){
    if(document.getElementById("register-qr-gen").checked && Object.keys(qr_inner).length !== 0){
        document.getElementById("register-qr").innerHTML = `<img src="https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=otpauth://totp/${qr_inner['u']}?secret=${qr_inner['x']}">`
        document.getElementById("register-qr-label").innerHTML = `Codigo Qr, escanealo con <a target="_blank" href="https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2&hl=es&gl=US">google authenticator</a> o con cualquier aplicacion o pagina que soporte la generacion de codigos totp a partir de llaves, como <a href="https://totp.danhersam.com/" target="_blank">esta por ejemplo</a> o copia y pega el secreto = <code>${qr_inner['x']}</code>`
    }else{
        document.getElementById("register-qr").innerHTML = ''
        //document.getElementById("register-qr-label").innerHTML = `Codigo Qr, (cuando registres un nuevo usuario saldra aqui), escanealo con <a target="_blank" href="https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2&hl=es&gl=US">google authenticator</a> o con cualquier aplicacion o pagina que soporte la generacion de codigos totp a partir de llaves, como <a href="https://totp.danhersam.com/" target="_blank">esta por ejemplo</a>.`
        document.getElementById("register-qr-label").innerHTML = ''
    }
}

function hosthandle(confirm){
    if (confirm){
        document.getElementById("host").value = DEF_HOST
        console.log("host restablecido a "+DEF_HOST+" correctamente")
    }else{
        host = document.getElementById("host").value
    }
}

function json_formatter(json_data){
    return "<pre>"+JSON.stringify(JSON.parse(json_data), null, 4)+"</pre>"
}

function json_post(data){
    return {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        'body':data,
    }
}

function login(confirm){
    let send_json = JSON.stringify({
        'u':document.getElementById("login-usuario").value,
        'k':document.getElementById("login-totp").value
    })
    document.getElementById("login-in").innerHTML=json_formatter(send_json)
    if (confirm){
        document.getElementById("login-statuscode").innerHTML = ''
        fetch(host+'/login',json_post(send_json))
        .then(response => {
            document.getElementById("login-statuscode").innerHTML = response.status.toString()+' '+response.statusText.toUpperCase()
            return response.json()
          })
        .then(responseData => {
            document.getElementById("login-out").innerHTML = json_formatter(JSON.stringify(responseData))
        })
        .catch(error => {
            console.warn(error)
            document.getElementById("login-out").innerHTML='{}'
        })
    }
}

function register(confirm){
    let user = document.getElementById("register-usuario").value
    let send_json = JSON.stringify({
        's' : document.getElementById("register-token").value,
        'u' : user,
        'a' : document.getElementById("register-access").value,
        'fn' : document.getElementById("register-fn").value,
        'ln' : document.getElementById("register-ln").value,
    })
    document.getElementById("register-in").innerHTML=json_formatter(send_json)
    qr_inner = {}
    qrmadein()
    if (confirm){
        document.getElementById("register-statuscode").innerHTML = ''
        fetch(host+'/register',json_post(send_json))
        .then(response => {
            document.getElementById("register-statuscode").innerHTML = response.status.toString()+' '+response.statusText.toUpperCase()
            return response.json()
          })
        .then(responseData => {
            document.getElementById("register-out").innerHTML = json_formatter(JSON.stringify(responseData))
            qr_inner = {"u":user,"x":responseData['x']}
            qrmadein()
        })
        .catch(error => {
            qr.innerHTML = ""
            console.warn(error)
            document.getElementById("register-out").innerHTML='{}'
        })
    }
}

function logout(confirm){
    let send_json = JSON.stringify({
        's':document.getElementById("logout-session").value
    })
    document.getElementById("logout-in").innerHTML=json_formatter(send_json)
    if (confirm){
        document.getElementById("logout-statuscode").innerHTML = ''
        fetch(host+'/logout',json_post(send_json))
        .then(response => {
            document.getElementById("logout-statuscode").innerHTML = response.status.toString()+' '+response.statusText.toUpperCase()
            return response.json()
          })
        .then(responseData => {
            document.getElementById("logout-out").innerHTML = json_formatter(JSON.stringify(responseData))
        })
        .catch(error => {
            console.warn(error)
            document.getElementById("logout-out").innerHTML='{}'
        })
    }
}

function unregister(confirm){
    let send_json = JSON.stringify({
        'u':document.getElementById("unregister-usuario").value,
        'k':document.getElementById("unregister-totp").value
    })
    document.getElementById("unregister-in").innerHTML=json_formatter(send_json)
    if (confirm){
        document.getElementById("unregister-statuscode").innerHTML = ''
        fetch(host+'/unregister',json_post(send_json))
        .then(response => {
            document.getElementById("unregister-statuscode").innerHTML = response.status.toString()+' '+response.statusText.toUpperCase()
            return response.json()
          })
        .then(responseData => {
            document.getElementById("unregister-out").innerHTML = json_formatter(JSON.stringify(responseData))
        })
        .catch(error => {
            console.warn(error)
            document.getElementById("unregister-out").innerHTML='{}'
        })
    }
}

function userinfo(confirm){
    function checkall(){
        document.getElementById("userinfo-id").checked = true
        document.getElementById("userinfo-user").checked = true
        document.getElementById("userinfo-name").checked = true
        document.getElementById("userinfo-lname").checked = true
        document.getElementById("userinfo-access").checked = true
        document.getElementById("userinfo-create").checked = true
        for (let i = 0; i < infolst.length ;  i++){
            info[infolst[i]]=true
        }
        userinfo(false)
    }
    let url_arguments = ''
    let session = document.getElementById("userinfo-session").value
    url_arguments += '/' + session
    let users = document.getElementById("userinfo-users").value
    let all_users = document.getElementById("userinfo-all-users").checked
    let infolst = ['id','u','fn','ln','a','ca']
    let info = {
        'id' : document.getElementById("userinfo-id").checked,
        'u' : document.getElementById("userinfo-user").checked,
        'fn' : document.getElementById("userinfo-name").checked,
        'ln' : document.getElementById("userinfo-lname").checked,
        'a' : document.getElementById("userinfo-access").checked,
        'ca' : document.getElementById("userinfo-create").checked
    }
    let limit = document.getElementById("userinfo-limit").value
    let offset = document.getElementById("userinfo-offset").value

    if(all_users){
        document.getElementById("userinfo-users").value = 'all'
        document.getElementById("userinfo-users").disabled = true
    }else{
        if(document.getElementById("userinfo-users").value == 'all'){
            document.getElementById("userinfo-users").disabled = false
            document.getElementById("userinfo-users").value = ''
        }
    }
    url_arguments += '?user='
    url_arguments += (users!='')?users:'all'
    url_arguments += '&info='
    let j = 0
    for (let i = 0; i < infolst.length ;  i++){
        if(info[infolst[i]]){
            j++
        }
    }
    if(j==0)checkall()
    let k = 0
    for (let i = 0; i <= infolst.length ;  i++){
        if (info[infolst[i]]){
            url_arguments += (k>0)?',':''
            url_arguments += infolst[i]
            k++
        }
    }
    if(limit!=100)url_arguments += '&limit=' + limit
    if(offset!=0)url_arguments += '&offset=' + offset
    document.getElementById("userinfo-in").innerHTML = '/userinfo' + url_arguments
    if(confirm==true){
        fetch(host+'/userinfo'+url_arguments)
        .then(response => {
            console.log(response.status)
            document.getElementById("userinfo-statuscode").innerHTML = response.status.toString()+' '+response.statusText.toUpperCase()
            return response.json()
          })
        .then(responseData => {
            document.getElementById("userinfo-out").innerHTML = json_formatter(JSON.stringify(responseData))
        })
        .catch(error => {
            console.warn(error)
            document.getElementById("userinfo-out").innerHTML='{}'
        })
    }else if (confirm==2){
        checkall()
    }
}

function test(confirm){
    let url_arguments = ''
    if(document.getElementById("test-url").value!=''){
        url_arguments+='/'+document.getElementById("test-url").value.replace(/,/g,'/')
    }
    if(document.getElementById("test-uri").value!=''){
        url_arguments+='?'+document.getElementById("test-uri").value.replace(/,/g,'&')
    }
    document.getElementById("test-in").innerHTML = '/test' + url_arguments
    if (confirm){
        document.getElementById("test-statuscode").innerHTML = ''
        fetch(host+'/test'+url_arguments)
        .then(response => {
            console.log(response.status)
            document.getElementById("test-statuscode").innerHTML = response.status.toString()+' '+response.statusText.toUpperCase()
            return response.json()
          })
        .then(responseData => {
            document.getElementById("test-out").innerHTML = json_formatter(JSON.stringify(responseData))
        })
        .catch(error => {
            console.warn(error)
            document.getElementById("test-out").innerHTML='{}'
        })
    }
}

function hostez(bool){
    //en desarrollo
    let prefix=`
    <br>
    <label>modo facil</label>
    <input type="checkbox" value="true" onchange="hostez()">
    `
    let sufix=`
        <table>
            <tr>
                <th>
                    Protocolo
                </th>
                <th></th>
                <th>
                    Direccion del servidor
                </th>
                <th></th>
                <th>
                    Puerto
                </th>
                <th></th>
                <th>
                    API Endpoint
                </th>
            </tr>
            <tr>
                <th>
                    <select id="protocol" onchange="hostez()">
                        <option>http</option>
                        <option>https</option>
                    </select>
                </th>
                <th>
                    <span>://</span>
                </th>
                <th>
                    <input type="text" id="hostin" placeholder="www.example.com" oninput="hostez()">
                </th>
                <th>
                    <span>:</span>
                </th>
                <th>
                    <input type="number" id="port" value="80" min="0" size="6" placeholder="80" oninput="hostez()">
                </th>
                <th>
                    <span>/</span>
                </th>
                <th>
                    <input type="text" id="endpoint" placeholder="api" oninput="hostez()">
                </th>
            </tr>
        </table>
    `
//document.getElementById("hostez").innerHTML=base
}