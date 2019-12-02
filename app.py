# To solve your task you might (or might not) need to import additional libraries
from flask import Flask, render_template, flash, redirect, url_for, request, logging
import requests as api_request
import json

app = Flask(__name__, static_url_path='/static')

# Headers for REST API call.
# Paste the API-key you have been provided as the value for "x-api-key"
headers = {
        "Content-Type": "application/json",
        "Accept": "application/hal+json",
        "x-api-key": "860393E332148661C34F8579297ACB000E15F770AC4BD945D5FD745867F590061CAE9599A99075210572"
        }

# Example of function for REST API call to get data from Lime
def get_api_data(headers, url):
	# First call to get first data page from the API
    response = api_request.get(url=url, headers=headers, data=None, verify=False)

    # Convert the response string into json data and get embedded limeobjects
    json_data = json.loads(response.text)
    limeobjects = json_data.get("_embedded").get("limeobjects")

    # Check for more data pages and get thoose too
    nextpage = json_data.get("_links").get("next")
    while nextpage is not None:
        url = nextpage["href"]
        response = api_request.get(url=url, headers=headers, data=None, verify=False)
        json_data = json.loads(response.text)
        limeobjects += json_data.get("_embedded").get("limeobjects")
        nextpage = json_data.get("_links").get("next")

    return limeobjects

# Index page
@app.route('/')
def index():
	return render_template('home.html')

# Deals page
@app.route('/dealData')
def dealData():
    # API call to get all agreed deals from 2018
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    params = "?dealstatus=agreement&min-closeddate=2018-01-01T00:00&max-closeddate=2018-12-31T23:59"
    url = base_url + params
    response_deals = get_api_data(headers=headers, url=url)
    # If we get data from the call
    if len(response_deals) > 0:

        deal_value = 0
        nr_deals = 0
        deals_month = {'01': 0,'02': 0,'03': 0,'04': 0,'05': 0,'06': 0,'07': 0,'08': 0,'09': 0,'10': 0,'11': 0,'12': 0,}

        # For each object in the call check its value and add it to a variable
        for item in response_deals:
            deal_value = deal_value + int(item['value'])
            nr_deals = nr_deals + 1

            # This loops through the numbers 1-12, makes them into strings and adds a "0" to all 1-digit numbers.
            # It then checks the objects closeddate, compares it to all months and adds the deal to the matched month
            for i in range(1, 13):
                if i < 10:
                    month = "0" + str(i)

                else:
                    month = str(i)

                temp_date = "2018-" + month

                if temp_date in item['closeddate']:
                    deals_month[month] += 1

        # Get the avarage value of all deals the last year
        avg_value = deal_value / nr_deals

        # Sends all the data we want to output to the template.
        deals = [{'name': '{:,}'.format(deal_value), 'title': "Total value"}, {'name': '{:,}'.format(round(avg_value)), 'title': "Avarage value"}, {'name': nr_deals, 'title': "Total deals"}]
        q1 = [{'month': "January", 'value': deals_month["01"]}, {'month': "February", 'value': deals_month["02"]}, {'month': "March", 'value': deals_month["03"]}]
        q2 = [{'month': "April", 'value': deals_month["04"]}, {'month': "May", 'value': deals_month["05"]}, {'month': "June", 'value': deals_month["06"]}]
        q3 = [{'month': "July", 'value': deals_month["07"]}, {'month': "August", 'value': deals_month["08"]}, {'month': "September", 'value': deals_month["09"]}]
        q4 = [{'month': "October", 'value': deals_month["10"]}, {'month': "November", 'value': deals_month["11"]}, {'month': "December", 'value': deals_month["12"]}]
        return render_template('mytemplate.html', items=deals, quarter1=q1, quarter2=q2, quarter3=q3, quarter4=q4)

    else:
        msg = 'No deals found'
        return render_template('mytemplate.html', msg=msg)

# Customer page
@app.route('/customers')
def customers():

    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    params = "?dealstatus=agreement&min-closeddate=2018-01-01T00:00&max-closeddate=2018-12-31T23:59"
    base_url1 = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/company/"
    params1 = "?not-_id=0"
    url = base_url + params
    response_deals = get_api_data(headers=headers, url=url)
    url = base_url1 + params1
    response_companies = get_api_data(headers=headers, url=url)

    if len(response_deals) and len(response_companies) > 0:

        customer_value = {}

        # For each deal agreed, check which company made it and how much it's worth
        for item in response_deals:

            temp_name = item['company']
            temp_value = item['value']

            # If no company was assigned do nothing
            if temp_name is None:
                pass
            # If there is already a deal by this company in the system add this deals value to that
            elif temp_name in customer_value:
                customer_value[temp_name] += temp_value
            # Else just add this company and the deal value to the dictionary
            else:
                customer_value[temp_name] = temp_value

        # Make a list of all companies and their deal values
        customerset = []
        for key, value in customer_value.items():
            for company in response_companies:
                if key == company['_id']:
                    customerset.append({'name': company['name'], 'value': '{:,}'.format(round(value))})
            # customerset.append({'name': key, 'value': '{:,}'.format(round(value))})

        # Send the list to the output template
        return render_template('mycustomers.html', customerdata=customerset)
    else:
        msg = 'No deals found'
        return render_template('mycustomers.html', msg=msg)

# Customer status
@app.route('/status')
def example():
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/company/"
    params = "?dealstatus=agreement&max-closeddate=2017-12-31T23:59"
    base_url1 = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    params1 = "?dealstatus=agreement&min-closeddate=2018-01-01T00:00"
    url = base_url
    response_companies = get_api_data(headers=headers, url=url)
    url = base_url1 + params
    pre_2018_deals = get_api_data(headers=headers, url=url)
    url = base_url1 + params1
    post_2018_deals = get_api_data(headers=headers, url=url)


    if len(response_companies) and len(pre_2018_deals) and len(post_2018_deals) > 0:

        customers = {}

        for customer in response_companies:
            customers[customer['_id']] = customer['name']

        current_customers = []
        previous_customers = []
        temp_prospects = set()
        prospects = []
        for key, value in customers.items():
            for deal in post_2018_deals:
                if key == deal['company']:
                    current_customers.append({'id': key, 'name': value})
                    break
            for deal in pre_2018_deals:
                if key == deal['company']:
                    previous_customers.append({'id': key, 'name': value})
                    break
        joined_list = current_customers + previous_customers

        for key, value in customers.items():
            for item in joined_list:
                if item['id'] != key:
                    temp_prospects.add(key)

        for key, value in customers.items():
            for prospect in temp_prospects:
                if key == prospect:
                    prospects.append({'id': key, 'name': value})

        sizes = [{'list': "current_customers", 'size': len(current_customers)}, {'list': "previous_customers", 'size': len(previous_customers)}, {'list': "prospects", 'size': len(prospects)}, {'list': "temp_prospects", 'size': len(temp_prospects)}, {'list': "customers", 'size': len(customers)}, {'list': "joined", 'size': len(joined_list)}]

        return render_template('example.html', customers=current_customers, inactives=previous_customers, prospects=prospects, sizes=sizes)
    else:
        msg = 'No deals found'
        return render_template('example.html', msg=msg)

# DEBUGGING
# If you want to debug your app, one of the ways you can do that is to use:
# import pdb; pdb.set_trace()
# Add that line of code anywhere, and it will act as a breakpoint and halt your application

if __name__ == '__main__':
	app.secret_key = 'somethingsecret'
	app.run(debug=True)
