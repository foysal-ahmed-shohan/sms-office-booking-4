at now we are going to work at final stege. so now the final booking system is static. we need to make it dynamic. now we have all ids . so now we can book slot at officernd spaces. apis sturcure and response is below

## api request: 
 curl --request GET \
     --url https://app.officernd.com/api/v2/organizations/agi-2/bookings \
     --header 'accept: application/json' \
     --header 'authorization: Bearer 871536ac46534fedf86da75266ea000946b90d11'

     
   ## output  {
  "rangeStart": 1,
  "rangeEnd": 50,
  "cursorNext": "eyJrIjoiX2lkIiwicCI6NTAsInYiOiI2ODQyYmUyZDNjODBkYzcxOGIzYmE4OTIifQ",
  "results": [
    {
      "_id": "6842be2d3c80dc718b3ba861",
      "timezone": "America/New_York",
      "start": "2021-07-19T14:00:00.000Z",
      "end": "2021-07-19T16:00:00.000Z",
      "fees": [],
      "recurrence": {
        "rrule": null
      },
      "reference": "R1DVV5D",
      "visitors": [],
      "members": [],
      "serviceSlots": {
        "before": 0,
        "after": 0
      },
      "createdAt": "2021-07-19T16:42:06.106Z",
      "createdBy": "5c98f3256f9ac200105a2700",
      "modifiedAt": "2021-07-19T16:43:00.167Z",
      "modifiedBy": "5c98f3256f9ac200105a2700"
    },
    {
      "_id": "6842be2d3c80dc718b3ba862",
      "timezone": "America/New_York",
      "start": "2021-07-19T13:00:00.000Z",
      "end": "2021-07-19T14:30:00.000Z",
      "fees": [],
      "recurrence": {
        "rrule": null
      },
      "reference": "8G69C5D",
      "visitors": [],
      "members": [],
      "serviceSlots": {
        "before": 0,
        "after": 0
      },
      "createdAt": "2021-07-19T16:43:19.770Z",
      "createdBy": "5c98f3256f9ac200105a2700",
      "modifiedAt": "2021-07-19T16:43:19.770Z",
      "modifiedBy": "5c98f3256f9ac200105a2700"
    },
    {
      "_id": "6842be2d3c80dc718b3ba892",
      "timezone": "America/New_York",
      "start": "2022-03-10T19:45:00.000Z",
      "end": "2022-03-10T20:45:00.000Z",
      "member": "6842be293c80dc718b3ba362",
      "fees": [],
      "recurrence": {
        "rrule": null
      },
      "reference": "HCP4X5N",
      "visitors": [],
      "members": [],
      "serviceSlots": {
        "before": 0,
        "after": 0
      },
      "createdAt": "2022-03-10T19:31:58.073Z",
      "createdBy": "5c98f3256f9ac200105a2700",
      "modifiedAt": "2022-03-10T19:31:58.073Z",
      "modifiedBy": "5c98f3256f9ac200105a2700"
    },


    this reponse you can see it has start and end date and time. so before booking please check user require free time is available or not. if free slot found that means no booking at this time and date then create a booking. below is booking create flow

    ### Booking creting flow:

    curl --request POST \
     --url https://app.officernd.com/api/v2/organizations/agi-2/bookings \
     --header 'accept: application/json' \
     --header 'authorization: Bearer 871536ac46534fedf86da75266ea000946b90d11' \
     --header 'content-type: application/json' \
     --data '
    {
    "start": "2025-10-31T13:00:00.000Z",
    "end": "2025-10-31T13:30:00.000Z",
    "resource": "6842be2a3c80dc718b3ba4b8",
    "description": "This booking done from officrnd sms booking system",
    "member": "684c7cc078775bf2b52dd162"
    }
    '

    output:

    {
  "_id": "684c86cc78775bf2b5307d6c",
  "timezone": "America/New_York",
  "start": "2025-10-31T13:00:00.000Z",
  "end": "2025-10-31T13:30:00.000Z",
  "location": "5e9b84959a6d250158f3cdf8",
  "member": "684c7cc078775bf2b52dd162",
  "resource": "6842be2a3c80dc718b3ba4b8",
  "fees": [
    {
      "date": "2025-10-31T00:00:00.000Z",
      "fee": "684c86cb78775bf2b5307d47",
      "extraFees": [],
      "passes": [],
      "credits": [],
      "coins": []
    }
  ],
  "recurrence": {
    "rrule": null
  },
  "reference": "XQMR573",
  "rate": "6842be293c80dc718b3ba345",
  "description": "This booking done from officrnd sms booking system",
  "isAccounted": true,
  "visitors": [],
  "members": [],
  "serviceSlots": {
    "before": 0,
    "after": 0
  },
  "createdAt": "2025-06-13T20:15:08.069Z",
  "createdBy": "6842bf627f86b53f5241868c"
}


this way booking will created. after done booking the booking id also add on reponse all_required_ids inside. you need to convert user date time with officerend requird formate. must follow my provided date time structure. otherwise booking will not insert. on curl request i give you how and what you need to send dynamically. 

what if booking time not free?
after retrieve all booking then check matching resources id then get all start and end time. if you can see user inserted date and time already booked . already booked this time then you have to ask again question to user that, this date and time not available. so please kindly choose another date time. then user will send their new date time, if it free then book a booking again if same resource id all booking list if alreay has booking on same date time then ask again for choosing new date time. this is the final stage. this last step it should work propelry. optimize, and good structure. dont do any mistake. 