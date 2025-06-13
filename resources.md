I want to add here one more thing, after user add space or room type then you need to ask like which type resource you need, like under meeting room there are some sube resources. below api and reponse you can get it idea. so basically after get room or space type you need to know the sub space type. suggestion is below 

request is : curl --request GET \
     --url https://app.officernd.com/api/v2/organizations/agi-2/resources \
     --header 'accept: application/json' \
     --header 'authorization: Bearer 19ec64f5c82b91ea07b0067d4f0a6461681729d8'

     output is:  {
  "rangeStart": 1,
  "rangeEnd": 24,
  "results": [
    {
      "_id": "6842be2a3c80dc718b3ba4b6",
      "name": "Booth 2",
      "description": "A small phone booth for calls.",
      "type": "meeting_room",
      "location": "5d1bcda0dbd6e40010479eec",
      "floor": "6842be293c80dc718b3ba407",
      "price": 0,
      "deposit": 0,
      "size": 1,
      "parents": [],
      "availability": {
        "startDate": "2020-04-20T00:00:00.000Z",
        "endDate": null
      },
      "images": [
        "//dzrjcxtasfoip.cloudfront.net/user-resources/organization/phone-booth-2-1587401176993.jpeg"
      ],
      "amenities": [],
      "createdAt": "2020-04-20T16:40:46.305Z",
      "createdBy": "5c98f3256f9ac200105a2700",
      "modifiedAt": "2024-04-11T13:00:49.340Z",
      "modifiedBy": "63bbdd40c347cf1006cdacba"
    },
    {
      "_id": "6842be2a3c80dc718b3ba4b7",
      "name": "Board Room",
      "description": "Our large room overlooking the Atlanta property.",
      "type": "meeting_room",
      "rate": "6842be293c80dc718b3ba345",
      "location": "5d1bcda0dbd6e40010479eec",
      "floor": "6842be293c80dc718b3ba407",
      "price": 0,
      "deposit": 0,
      "size": 8,
      "parents": [],
      "availability": {
        "startDate": "2020-04-20T00:00:00.000Z",
        "endDate": null
      },
      "images": [
        "//dzrjcxtasfoip.cloudfront.net/user-resources/organization/board-room-1648749580592.png"
      ],
      "amenities": [
        "6842be293c80dc718b3ba328",
        "6842be293c80dc718b3ba329",
        "6842be293c80dc718b3ba32a"
      ],
      "createdAt": "2020-04-20T16:40:59.623Z",
      "createdBy": "5c98f3256f9ac200105a2700",
      "modifiedAt": "2024-04-11T13:00:49.322Z",
      "modifiedBy": "63bbdd40c347cf1006cdacba"
    },
    {
      "_id": "6842be2a3c80dc718b3ba4b8",
      "name": "Zoom Room",
      "description": "Our Zoom Equipped Large Meeting Room",
      "type": "meeting_room",
      "rate": "6842be293c80dc718b3ba345",
      "location": "5e9b84959a6d250158f3cdf8",
      "price": 0,
      "deposit": 0,
      "size": 6,
      "parents": [],
      "availability": {
        "startDate": "2020-04-20T00:00:00.000Z",
        "endDate": null
      },
      "images": [
        "//dzrjcxtasfoip.cloudfront.net/user-resources/organization/zoom-room-1587401387574.png"
      ],
      "amenities": [
        "6842be293c80dc718b3ba328",
        "6842be293c80dc718b3ba329",
        "6842be293c80dc718b3ba32a"
      ],
      "createdAt": "2020-04-20T16:48:08.535Z",
      "createdBy": "5c98f3256f9ac200105a2700",
      "modifiedAt": "2024-04-11T13:00:49.315Z",
      "modifiedBy": "63bbdd40c347cf1006cdacba"
    },
    {
      "_id": "6842be2a3c80dc718b3ba4b9",
      "name": "Booth 1",
      "description": "A small 1 person phone booth with power and AC.",
      "type": "meeting_room",
      "location": "5d1bcda0dbd6e40010479eec",
      "floor": "6842be293c80dc718b3ba407",
      "price": 0,
      "deposit": 0,
      "size": 1,
      "parents": [],
      "availability": {
        "startDate": "2020-04-20T00:00:00.000Z",
        "endDate": null
      },
      "images": [
        "//dzrjcxtasfoip.cloudfront.net/user-resources/organization/phone-booth-1-1587401155459.jpeg"
      ],
      "amenities": [],
      "createdAt": "2020-04-20T16:40:34.363Z",
      "createdBy": "5c98f3256f9ac200105a2700",
      "modifiedAt": "2024-04-11T13:00:49.325Z",
      "modifiedBy": "63bbdd40c347cf1006cdacba"
    },



    dynamically you have to call api and get the response. you can see every type of like  "type": "meeting_room", has different type  of name and description. so suponse if user chose meeting room then suggest them to chose resources . give then name with description. when user chose then take the id of the resources. this resources id show me after user confirm the booking. thats it. like with booking also give me this resource id . that it 
    
    "name": "Booth 1",
      "description": "A small 1 person phone booth with power and AC.",