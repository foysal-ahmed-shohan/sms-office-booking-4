when user confirm or say yes and cofirm then now we are going to booking real booking . dynamically booking at officernd. I am going to tell you how it will work. 

for booking officernd its need member on company id and . so before book, we need to check this phone number has member or compnay has or not. need to get those members list and compnay list. if user number match or found then take the id. if member found then take members id, if company found then take the company id.  so not found any company or member with match of the number then need to create member . so after member create you can also get member id. so retrive member , company and create member api and their response is below

Memerrs retrive:

curl --request GET \
     --url https://app.officernd.com/api/v2/organizations/agi-2/members \
     --header 'accept: application/json' \
     --header 'authorization: Bearer 0f53be465287e5766d26b95a935aa58ff6494d41'

     response will get : 