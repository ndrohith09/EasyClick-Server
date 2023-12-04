from rest_framework.response import Response

'''Response Contents'''
def display_response(msg,err,body,statuscode,request=None):
    response = Response({
                "MSG":msg,
                "ERR":err,
                "BODY":body
            },status=statuscode)
    
    
    if request and  "origin" in request.headers.keys():
        response["Access-Control-Allow-Origin"] = request.headers["origin"]
        response["Access-Control-Allow-Methods"]=["GET","POST","PUT","DELETE","PATCH","OPTIONS"]
    else:
        response["Access-Control-Allow-Origin"]="*"
    return response

'''Success message'''
SUCCESS = "Action Performed Succesfully"


'''Error Exception Message'''
def exceptiontype(exception):
    return "Type: {}".format(type(exception).__name__)

def exceptionmsg(exception):
    return "Msg: {}".format(exception)