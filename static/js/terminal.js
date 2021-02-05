// build terminal emulator
let prompt = "~$ ";
let term = new Terminal();
term.setOption('cursorBlink', true);
term.open(document.getElementById('xterminal'));

// run terminal emulator
let input = "";
let shellHistory = [];
let shellHistoryIndex = 0;
term.onData(function(data) {
 const code = data.charCodeAt(0);
 if(code === 13) {
     if (input !== "" && !checkSpecialKeywords(input)) {
         runCommand(input);
         shellHistory.pop();
         shellHistory.push(input);
         shellHistory.push("");
         shellHistoryIndex = shellHistory.length - 1;
     } else {
         term.write('\r\n' + prompt + ' ');
     }
     input = "";
 } else if (code === 127) {
     if (input.length > 0) {
         term.write("\b \b");
         input = input.substr(0, input.length - 1);
     }
     return;
 } else if (code === 27) {
    updateHistory(data);
 } else if (code < 32) {
     return;
 } else {
     term.write(data);
     input += data;
 }
});

function updateHistory(data) {
    if (shellHistory.length > 0) {
        if (data.localeCompare("[A") === 0) {
            handleUpArrow();
        } else if (data.localeCompare("[B") === 0){
            handleDownArrow();
        }
    }
}

function handleUpArrow(){
    if (shellHistoryIndex > 0) {
        shellHistoryIndex--;
        writeHistory(shellHistory[shellHistoryIndex]);
    }
}

function handleDownArrow() {
    if (shellHistoryIndex < shellHistory.length - 1){
        shellHistoryIndex++;
        writeHistory(shellHistory[shellHistoryIndex]);
    }
}

function writeHistory(value) {
    term.write('\33[2K\r' + prompt + " ");
    term.write(value);
    input = value;
}

function getShellHistory(elem) {
    restRequest('POST', {'paw':elem.options[elem.selectedIndex].getAttribute('data-paw')}, populateHistory, endpoint='/plugin/manx/history');
}

function populateHistory(data) {
    if (data.length > 0){
        for (let index in data) {
            shellHistory.push(data[index]['cmd']);
        }
        shellHistory.push("");
        shellHistoryIndex = shellHistory.length - 1;
    }
}

function displayHistory() {
    for (let i = 0; i < shellHistory.length - 1; i++) {
        term.write('\r\n['+i+']  ' +shellHistory[i]);
    }
}

function checkSpecialKeywords(word) {
    if (word.localeCompare("history") === 0) {
        console.log("displaying history");
        displayHistory();
        return true
    }
    return false
}

function runCommand(input) {
 let sessionId = $('#session-id option:selected').attr('value');
 var [wsHost, wsPort] = $('#websocket-data').data('websocket').split(':');

 if (wsHost === '0.0.0.0'){
    console.log('WebSocket host configured for 0.0.0.0. Using window location for host/ip instead.');
    wsHost = window.location.hostname;
 }

 var socket = new WebSocket('ws://' + wsHost + ':' + wsPort + '/manx/' + sessionId);

 socket.onopen = function () {
     socket.send(input);
 };

 socket.onmessage = function (s) {
     try {
         let jData = JSON.parse(s.data);
         let lines = jData["response"].split('\n');
         for(let i = 0;i < lines.length;i++){
            term.write("\r\n"+lines[i]);
         }
         prompt = jData["pwd"];
         term.write("\r\n"+prompt+'$ ');
     } catch(err){
         term.write("\r\n"+'Dead session. Probably. It has been removed.');
         clearTerminal();
         $('#session-id option:selected').remove();
     }
 };
}

function displayCommand(){
    function displayMe(data){
        $('#delivery-command-terminal').text(atob(data[0].test));
    }
    let cmd = $('#dcommands-terminal option:selected');
    stream('Great, you picked '+cmd.text()+'. Now run the command on the host. It will run in the background - but you can change this if you would like.');
    restRequest('POST', {'index':'abilities','ability_id':cmd.val(),'platform':cmd.text()}, displayMe);
}

// ability filter options

let ABILITIES = [];
function getAbilities() {
 function getAbilitiesCallback(data){
    $('#tactic-filter').empty().append("<option disabled='disabled' selected>Choose a tactic</option>");
     ABILITIES = [];
     let found = [];
     data.abilities.forEach(function(ability) {
         ABILITIES.push(ability);
         if(!found.includes(ability.tactic)) {
             $('#tactic-filter').append('<option value="'+ability.tactic+'">'+ability.tactic+'</option>');
             found.push(ability.tactic);
         }
     });
 }
 restRequest('POST', {"paw": $('#session-id option:selected').data('paw')}, getAbilitiesCallback, '/plugin/manx/ability');
}
function filterTechniques() {
 let found = [];
 $('#technique-filter').empty().append("<option disabled='disabled' selected>Choose a technique</option>");
 ABILITIES.forEach(function(ability){
     if(ability.tactic === $('#tactic-filter').val() && !found.includes(ability.technique_id)) {
         $('#technique-filter').append('<option value="'+ability.technique_id+'">'+ability.technique_id+' | '+ability.technique_name+'</option>');
         found.push(ability.technique_id);
     }
 });
}
function filterProcedures() {
    $('#procedure-filter').empty().append("<option disabled='disabled' selected>Choose a procedure</option>");
        ABILITIES.forEach(function(ability){
         if(ability.tactic === $('#tactic-filter').val() && ability.technique_id === $('#technique-filter').val()) {
             $('#procedure-filter').append('<option value="'+ability.ability_id+'">'+ability.name+'</option>');
         }
    });
}
function showProcedure() {
    function displayProcedure(data){
        for (let ab of data) {
            let agent = $('#session-id option:selected');
            if (ab.platform === agent.data("platform") && agent.data("executor") === ab.executor) {
                term.write(atob(ab.test));
                input = atob(ab.test);
                return;
            }
        }
        stream('No ability available for this agent\'s platform an executor combination');
    }
    restRequest('POST', {'index':'abilities','ability_id':$('#procedure-filter').val()}, displayProcedure)
}

function clearTerminal(){
    term.write('\33[2K\r');
    term.clear();
    shellHistory = [];
    shellHistoryIndex = 0;
    input = "";
    prompt = '~$ ';
    term.write("\r\n"+prompt+" ");
}

//# sourceURL=manxterm.js