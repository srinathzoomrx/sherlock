document.getElementById("send_response").style.display = 'none';
document.getElementById("select_option").style.display = 'none';
document.getElementById("result").style.display = 'none';
document.getElementById("reloader").style.display = 'none';
var http_response = "";
var options_i = 0;
var chosen_options = [];

/*
getResponse() is called when clicked on Submit button (question submission).
This function will invoke doGET() from server to get either ambiguous json or answer 
in the form of table.
If the obtained entity is a ambiguous json, then getOptions is called.
*/
function getResponse()
{
	var httpRequest = new XMLHttpRequest();
    httpRequest.onreadystatechange = function()
    {
        if (this.readyState == 4 && this.status == 200) 
        {
        	var ques = "<p><b>Question:</b><br>" 
            ques += document.getElementById("question_box").value + "<br></p>";
        	document.getElementById("display_question").innerHTML = ques;
            http_response = JSON.parse(this.responseText)
            if(http_response['type'] == 'options')
            {
            	getOptions();
            }
            else if(http_response['type'] == 'answer')
            {
                // construct_table(http_response);
            	var res = "Result in Table form will be displayed here";
            	document.getElementById("result").innerHTML += res;
                document.getElementById("result").style.display = 'block';
                document.getElementById("reloader").style.display = 'block';

	        }
        }
    };
    httpRequest.open("GET", "?question=" + document.getElementById("question_box").value, true);
    httpRequest.setRequestHeader("Content-Type", "application/json");
    httpRequest.send();
}

/*
getNextOption() will formulate the input element for the options of ambiguity.
This first calls push_previous_options() to store the previously selected option by the user.
*/
function getNextOption()
{
    push_previous_options();
    if(options_i < http_response['data'].length - 1)
    {
        innerHTML = "<b>Options:</b><br><form>";
        for(var j = 0; j < http_response['data'][options_i]['options'].length; j++)
        {
            innerHTML += "<input type=\"radio\" ";
            innerHTML += "name=\"option\" ";
            innerHTML += "value=\"" + http_response['data'][options_i]['value'] + "\" ";
            innerHTML += "id=\"" + j + "\">";
            innerHTML += "" + http_response['data'][options_i]['options'][j] + "</input><br />";
        }
        innerHTML += "</form>";
        document.getElementById("choices").innerHTML = innerHTML;
        options_i++;
    }
    else if(options_i == http_response['data'].length - 1)
    {
        document.getElementById("select_option").style.display = 'none';
        document.getElementById("send_response").style.display = 'block';
        innerHTML = "<b>Options:</b><br><form>";
        for(var j = 0; j < http_response['data'][options_i]['options'].length; j++)
        {
            innerHTML += "<input type=\"radio\" ";
            innerHTML += "name=\"option\" ";
            innerHTML += "value=\"" + http_response['data'][options_i]['value'] + "\" ";
            innerHTML += "id=\"" + j + "\">";
            innerHTML += "" + http_response['data'][options_i]['options'][j] + "</input><br />";
        }
        innerHTML += "</form>";
        document.getElementById("choices").innerHTML = innerHTML;
        options_i++;
    }
    else
    {
        document.getElementById("select_option").style.display = 'none';
        document.getElementById("send_response").style.display = 'block';
    }
}

/*
getOptions function is used to hide the submit button and display the next option button.
This function inturn will call the getNextOption().
*/
function getOptions()
{
	document.getElementById("submit_query").style.display = 'none';
	document.getElementById("select_option").style.display = 'block';
    getNextOption();
}

/*
push_previous_options() is used to get the choice selected by the user.
The selected options are appended in a list named chosen_options, which is global.
When options_i == 0, it means it has nothing to push and will be inactive
and go back to getNextOption() without any actual task.
*/
function push_previous_options()
{
    if(options_i != 0)
    {
        var choice = 0;
        var var_temp_id = "";
        for(var i = 0; i < http_response['data'][options_i - 1]['options'].length; i++)
        {
            var_temp_id = "" + i;
            if(document.getElementById(var_temp_id).checked)
            {
                choice = "" + document.getElementById(var_temp_id).id;
                chosen_options.push(choice);
                break;
            }
        }
    }
}

/*
sendOptions() will send the options selected by the user back to server for processing the
ambiguos phrases.
Eg: $0$1 code
*/
function sendOptions()
{
	var choice = 0;
    var var_temp_id = "";
    for(var i = 0; i < http_response['data'][options_i - 1]['options'].length; i++)
    {
        var_temp_id = "" + i;
        if(document.getElementById(var_temp_id).checked)
        {
        	choice = "" + document.getElementById(var_temp_id).id;
            chosen_options.push(choice);
            break;
        }
    }
    var httpRequest = new XMLHttpRequest();
    var resposes_of_user = "";
    httpRequest.onreadystatechange = function()
    {
        if (this.readyState == 4 && this.status == 200) 
        {
            http_response = JSON.parse(this.responseText)
            if(http_response['type'] == 'answer')
            {
                //construct_table(http_response);
                var res = "Result in Table form will be displayed here";
                document.getElementById("result").innerHTML += res;
                document.getElementById("result").style.display = 'block';
                document.getElementById("reloader").style.display = 'block';

            }
        }
    };
    for(var j = 0; j < chosen_options.length; j++)
    {
        resposes_of_user += chosen_options[j] + "$";
    }
    resposes_of_user += http_response['id']
    httpRequest.open("GET", "?user_response=" + resposes_of_user, true);
    httpRequest.setRequestHeader("Content-Type", "application/json");
    httpRequest.send();
    document.getElementById("send_response").style.display = 'none';
}

function getTable(response) {
    table = "<center><table>"
    for (var i = 0; i < response.length; i++) {
        table = table + "<tr>"
        for (var j = 0; j < response[i].length; j++) {
            table = table + "<td>" + response[i][j] + "</td>"
        }
        table = table + "</tr>"
    }
    table += "</table></center>"
    return table
}

function getList(response) {
    list = ""
    for (var i = 0; i < response.length; i++) {
        list += response[i][0] + "<br>"
    }
    return list
}

function construct_table(http_response)
{
    for (var i = http_response.length - 1; i >= 0; i--) {
        if ("query" in http_response[i]) {
            innerHTML = innerHTML + '<div class="query">Error:' + http_response[i]['query'] + "</div>"
        }
        if ("components" in http_response[i]) {
            innerHTML = innerHTML + '<div class="components">' + http_response[i]['components'] + "</div>"
        }
        if ("error" in http_response[i]) {
            innerHTML = innerHTML + '<div class="error">' + http_response[i]['error'] + "</div>"
        }
        if ("response" in http_response[i]) {
            response = http_response[i]['response']
            innerHTML = innerHTML + '<div class="response">'
            if (response.length > 1 && response[0].length > 1) {
                innerHTML += getTable(response)
            } else if (response.length > 1 && response[0].length == 1) {
                innerHTML += getList(response)
            } else if (response.length == 1 && response[0].length == 1) {
                innerHTML += response[0][0]
            } else {
                innerHTML += "None"
            }
            innerHTML += "</div>"
        }
    }
    document.getElementById("result").innerHTML = innerHTML
    document.getElementById("result").style.display = 'block';
}