import os
from twilio import api

# List Calls
#for call in api.calls:
#    print call

client = api.Client()

# Filter Calls
for call in client.calls.values(to="+5305451766", start_time="2010-04-01"):
    print call

# Get an Item
key = "CAaf0c49374b67e65717c398b2d6a72cdb"
call = client.calls[key]
call = client.calls.get(key)

print call.sid
print call.recordings

#account = client.sms_messages.[os.environ["TWILIO_ACCOUNT_SID"]]

# Update an Iteam
call = client.calls[key]
#call.update(key="foo")
