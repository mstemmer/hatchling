class ReportStatus:


def status_read(temp, humid, set_temp, set_humid) :
    if temp >= set_temp - oor_temp_a and temp <= set_temp + oor_temp_a and \
        humid >= set_humid - oor_humid_a and humid <= set_humid + oor_humid_a:
        status = mode[1]
        return status
    elif temp >= set_temp - oor_temp_b and temp <= set_temp + oor_temp_b and \
        humid >= set_humid - oor_humid_a and humid <= set_humid + oor_humid_a:
        status = mode[2]
        return status
    elif temp >= set_temp - oor_temp_c and temp <= set_temp + oor_temp_c and \
        humid >= set_humid - oor_humid_a and humid <= set_humid + oor_humid_a:
        status = mode[3]
        return status
    elif temp >= set_temp - oor_temp_d and temp <= set_temp + oor_temp_d and \
        humid >= set_humid - oor_humid_a and humid <= set_humid + oor_humid_a:
        status = mode[4]
        return status
    elif temp >= set_temp - oor_temp_a and temp <= set_temp + oor_temp_a and \
        humid >= set_humid - oor_humid_b and humid <= set_humid + oor_humid_b:
        status = mode[5]
        return status
    elif temp >= set_temp - oor_temp_b and temp <= set_temp + oor_temp_b and \
        humid >= set_humid - oor_humid_b and humid <= set_humid + oor_humid_b:
        status = mode[6]
        return status
    elif temp >= set_temp - oor_temp_c and temp <= set_temp + oor_temp_c and \
        humid >= set_humid - oor_humid_b and humid <= set_humid + oor_humid_b:
        status = mode[7]
        return status
    elif temp >= set_temp - oor_temp_d and temp <= set_temp + oor_temp_d and \
        humid >= set_humid - oor_humid_b and humid <= set_humid + oor_humid_b:
        status = mode[8]
        return status
    elif temp >= set_temp - oor_temp_a and temp <= set_temp + oor_temp_a and \
        humid >= set_humid - oor_humid_c and humid <= set_humid + oor_humid_c:
        status = mode[9]
        return status
    elif temp >= set_temp - oor_temp_b and temp <= set_temp + oor_temp_b and \
        humid >= set_humid - oor_humid_c and humid <= set_humid + oor_humid_c:
        status = mode[10]
        return status
    elif temp >= set_temp - oor_temp_c and temp <= set_temp + oor_temp_c and \
        humid >= set_humid - oor_humid_c and humid <= set_humid + oor_humid_c:
        status = mode[11]
        return status
    elif temp >= set_temp - oor_temp_d and temp <= set_temp + oor_temp_d and \
        humid >= set_humid - oor_humid_c and humid <= set_humid + oor_humid_c:
        status = mode[12]
        return status
    elif temp >= set_temp - oor_temp_a and temp <= set_temp + oor_temp_a and \
        humid >= set_humid - oor_humid_d and humid <= set_humid + oor_humid_d:
        status = mode[13]
        return status
    elif temp >= set_temp - oor_temp_b and temp <= set_temp + oor_temp_b and \
        humid >= set_humid - oor_humid_d and humid <= set_humid + oor_humid_d:
        status = mode[14]
        return status
    elif temp >= set_temp - oor_temp_c and temp <= set_temp + oor_temp_c and \
        humid >= set_humid - oor_humid_d and humid <= set_humid + oor_humid_d:
        status = mode[15]
        return status
    else :
        status = mode[16]
        return status

def shift_out(dPin,cPin,order,val): #shift_out function, use bit serial transmission.
    for i in range(0,8):
        GPIO.output(cPin,GPIO.LOW);
        if(order == LSBFIRST):
            GPIO.output(dPin,(0x01&(val>>i)==0x01) and GPIO.HIGH or GPIO.LOW)
        elif(order == MSBFIRST):
            GPIO.output(dPin,(0x80&(val<<i)==0x80) and GPIO.HIGH or GPIO.LOW)
        GPIO.output(cPin,GPIO.HIGH);

def status_out(status): #74HC595 will update the data to the parallel output port.
    GPIO.output(latchPin,GPIO.LOW)  #Output low level to latchPin
    shift_out(dataPin,clockPin,LSBFIRST,status) #Send serial data to 74HC595
    GPIO.output(latchPin,GPIO.HIGH) #Output high level to latchPin
    time.sleep(0.1)
