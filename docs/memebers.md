when user confirm or say yes and cofirm then now we are going to booking real booking . dynamically booking at officernd. I am going to tell you how it will work. 

for booking officernd its need member on company id and . so before book or booking at final stage, we need to check this phone number has member or compnay has or not. need to get those members list and compnay list. if user number match or found then take the id. if member found then take members id, if company found then take the company id.  so not found any company or member with match of the number then need to create member . so after member create you can also get member id. so retrive member , company and create member api and their response is below

Memerrs retrive:

curl --request GET \
     --url https://app.officernd.com/api/v2/organizations/agi-2/members \
     --header 'accept: application/json' \
     --header 'authorization: Bearer 0f53be465287e5766d26b95a935aa58ff6494d41'

     response will get : 

     {
  "rangeStart": 1,
  "rangeEnd": 17,
  "results": [
    {
      "properties": {},
      "_id": "6842be293c80dc718b3ba356",
      "name": "Jim Halpert",
      "location": "5d1bcda0dbd6e40010479eec",
      "company": "6842be293c80dc718b3ba351",
      "status": "active",
      "createdAt": "2020-04-20T15:56:38.933Z",
      "modifiedAt": "2020-04-20T15:57:31.223Z"
    },
    {
      "properties": {},
      "_id": "6846d88578775bf2b5fe2039",
      "name": "foysal",
      "location": "5d1bcda0dbd6e40010479eec",
      "status": "contact",
      "startDate": "2025-06-09T12:49:59.221Z",
      "createdAt": "2025-06-09T12:50:13.897Z",
      "modifiedAt": "2025-06-09T12:50:13.996Z"
    },
    {
      "properties": {
        "phone": "01682786501"
      },
      "_id": "6847096b78775bf2b5ff4068",
      "name": "Foysal Ahmed",
      "location": "5e9b84959a6d250158f3cdf8",
      "status": "contact",
      "startDate": "2026-06-09T12:49:59.221Z",
      "createdAt": "2025-06-09T16:18:51.071Z",
      "modifiedAt": "2025-06-09T16:18:51.266Z"
    }
  ]
}

inside properties you will get phone or mobile number. its a custom field so name is depend. with this you have to match mobile number. user probably added with country code with the number. with or without, both case possible

 "properties": {
        "phone": "01682786501"
      },


### Company:
curl --request GET \
     --url https://app.officernd.com/api/v2/organizations/agi-2/companies \
     --header 'accept: application/json' \
     --header 'authorization: Bearer 0f53be465287e5766d26b95a935aa58ff6494d41'


{
  "rangeStart": 1,
  "rangeEnd": 9,
  "results": [
    {
      "properties": {},
      "_id": "6842be293c80dc718b3ba34d",
      "startDate": "2020-04-18T00:00:00.000Z",
      "location": "5d1bcda0dbd6e40010479eec",
      "name": "Vance Refridgeration",
      "description": "Refrigeration Company that focuses on customer service!",
      "status": "active",
      "createdAt": "2020-04-19T00:16:20.467Z",
      "createdBy": "5c98f3256f9ac200105a2700",
      "modifiedAt": "2023-03-28T02:51:49.293Z",
      "modifiedBy": "5c98f3256f9ac200105a2700"
    },
    {
      "properties": {
        "phone": "01111111111"
      },
      "_id": "684c743b78775bf2b52c46cb",
      "startDate": "2025-06-09T12:49:59.221Z",
      "location": "5d1bcda0dbd6e40010479eec",
      "name": "foysal-it",
      "status": "inactive",
      "createdAt": "2025-06-13T18:55:55.136Z",
      "createdBy": "6842bf627f86b53f5241868c",
      "modifiedAt": "2025-06-13T18:55:55.136Z",
      "modifiedBy": "6842bf627f86b53f5241868c"
    }
  ]
}

inside properties you will get phone number or mobile number. its a custom field so name is depend for different account. user probably added with country code with the number. with or without, both case possible

{
      "properties": {
        "phone": "01111111111"
      },


 if nowhere match the mobile number then that means this is new user. so we will create new member. like below. then we can find the member id.


 ### create member if mobile numbernot match

 Add members:

curl --request POST \
     --url https://app.officernd.com/api/v2/organizations/agi-2/members \
     --header 'accept: application/json' \
     --header 'authorization: Bearer 2421b608ced7494c9073dadae36d3ef38fef5e19' \
     --header 'content-type: application/json' \
     --data '
{
  "properties": {
    "phone": "01682786501"
  },
  "name": "Foysal Ahmed",
  "location": "603dfbc260f4054084125d39",
  "startDate": "2025-06-09T12:49:59.221Z",
  "description": "This guest came from officernd sms booking system"
}


look carefully the date. it should current date . and also location id you will get when you choose location to user and they will selecte the location. so need here those field. same way you need to add member. then you will find the member id. so at last you need to show member id or company id reserouce id and booking id at last response. now only member id and compnay id is missing


## propelry handle all error. dont break other logic. dont break chat system inteligency. properly optimize and use all api endpoint in proper file. dont make any file more that 500 lines
