from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import IntegrityError, OperationalError
from django.http import JsonResponse
from rest_framework import status
from django.db import connections
from urllib.parse import quote, unquote
import traceback
from urllib.parse import quote, unquote
import json



class withdrawalAPIView(APIView):
    def post(self, request):
        raw_sql = request.data.get('query')  # Extract the actual SQL string
        if not raw_sql:
            return Response(
                {"error": "Missing 'query' in request body"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with connections['aptent_dev'].cursor() as cursor:
                cursor.execute(raw_sql)

                inserted_id = cursor.lastrowid

                cursor.execute(
                    "SELECT * FROM aptent_dev.transaction_record WHERE id = %s", 
                    [inserted_id]
                )

                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                result = dict(zip(columns, row)) if row else {}

            return Response(
                { "message": "Query executed successfully", "result": result },
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError as ie:
            return JsonResponse({"status": "failure", "error": "Integrity error: " + str(ie)}, status=500)
        except OperationalError as oe:
            return JsonResponse({"status": "failure", "error": "Operational error: " + str(oe)}, status=500)
        except Exception as e:
            return JsonResponse({"status": "failure", "error": str(e)}, status=500)

withdrawal_api_view = withdrawalAPIView.as_view()

# def encode_decode(request):
#     encoded = quote(request, safe='')
#     print("encoded: ", encoded)

#     decoded = unquote(encoded)
#     print(decoded)

class settlementBatchesAPIView(APIView):
    def get(self, request, *args, **kwargs):
        print("request>>>", request.query_params)
        amount = request.query_params.get('amount')
        stan = request.query_params.get('stan')

        data = {}
        try:
            with connections['default'].cursor() as cursor:
                # Get the latest withdrawal
                cursor.execute(
                    # "SELECT * FROM monnify_agency_banking.withdrawal_transactions ORDER BY created_on DESC LIMIT 1"

                    "SELECT * FROM withdrawal_transactions WHERE amount = %s AND system_trace_audit_number = %s", # add date
                    [amount, stan]
                )
                row = cursor.fetchone()

                if row:
                    # build dict with column names
                    columns = [col[0] for col in cursor.description]
                    data = dict(zip(columns, row))
                
                # Extract the transaction_reference if it exists
                transaction_reference = data.get('transaction_reference')
                print('transaction_reference:', transaction_reference)
                if not transaction_reference:
                    return Response({"error": "No transaction_reference found, Transaction failed!!!"}, status=404)

                # Run second query
                cursor.execute(
                    "SELECT * FROM settlement_batches WHERE originating_transaction_reference = %s",
                    [transaction_reference]
                )
                rows = cursor.fetchall()

                if not rows:
                    print("error: No settlement batch found")
                    return Response({"error": "No settlement batch found"}, status=404)

                columns2 = [col[0] for col in cursor.description]
                batches = [dict(zip(columns2, r)) for r in rows]

                return Response({
                    "settlement_batches": batches
                })

        except Exception as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)

settlement_batch_api_view = settlementBatchesAPIView.as_view()


class settlementEntriesAPIView(APIView):
    def get(self, request, *args, **kwargs):
        print(request.query_params)
        batch_id = request.query_params.get('id')
        scheme_id = str(request.query_params.get('business_scheme_id'))

        try:
            with connections['default'].cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM monnify_agency_banking.settlement_entries WHERE settlement_batch_id = %s",
                    [batch_id]
                )
                rows = cursor.fetchall()

                if not rows:
                    print("error: No settlement entries found")
                    return Response({"error": "No settlement batch found"}, status=404)
                
                columns = [col[0] for col in cursor.description]
                entries = [dict(zip(columns, r)) for r in rows]

                results = {}

                for e in entries:
                    participant_code = e.get("settlement_participant_type_code")
                    txn_type = e.get("transaction_type")
                    amount = e.get('settlement_amount')
                    
                    if participant_code not in results:
                        # initialize structure once
                        results[participant_code] = [
                            {'transaction_type': txn_type},
                            {'settlement_amount': [str(amount)]}  # list to hold multiple amounts
                        ]
                    else:
                        # append to existing list
                        results[participant_code][1]['settlement_amount'].append(str(amount))
                
                print("results: ", json.dumps(results, indent=2))
                return Response(
                    {"entry": results}
                )

        except Exception as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)


settlement_entries_api_view = settlementEntriesAPIView.as_view()


class AirKafkaAPIView(APIView):
    def put(self, request, *args, **kwargs):
        lastrowid = request.query_params.get('id')
        print("row_id: ", request.query_params)

        transaction_data = request.data  # <— now we get JSON body correctly

        print("transaction_data:", json.dumps(transaction_data, indent=2))

        # Ensure ID is provided
        if not lastrowid:
            return Response({"error": "Missing 'id' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connections['aptent_dev'].cursor() as cursor:
                query = """
                    UPDATE aptent_dev.transaction_record
                    SET sink_card_acceptor_id = %s,
                        message_name = %s
                    WHERE id = %s;
                """
                cursor.execute(query, ['', 'PURCHASE', lastrowid])
            print("updated ✅✅")
            return Response({"message": f"✅✅ successfully Updated sinkCardAcceptorId to NULL {lastrowid}"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# URL dispatcher binding
air_kafka_api_view = AirKafkaAPIView.as_view()




# Bro, I feel you — at first glance it **looks intimidating**, but let me break it down **into super simple, bite-sized pieces**, so you see it’s actually very doable.

# ---

# # ✅ **Truth: It’s not as hard as it looks**

# There are three main pieces to a WhatsApp automation bot:

# 1. **WhatsApp connection** – your bot “listens” to messages
# 2. **Automation logic** – your PyDoll scripts that do the bank tasks
# 3. **Response system** – your bot replies, sends files, buttons, reports

# Once you see it like this, it’s just **Python + PyDoll + API calls**, nothing else.

# ---

# # ⭐ **Step 1: Connect WhatsApp to Python**

# You don’t need to build WhatsApp itself — you just use **WhatsApp Cloud API** (official) or **Baileys library** (open source).

# * Meta’s API gives you a URL (webhook)
# * Your Python script “listens” to incoming messages
# * Incoming messages = triggers for your automation

# **Time needed:** ~1–2 hours to set up basic webhook

# ---

# # ⭐ **Step 2: Link to PyDoll scripts**

# * Your PyDoll automation scripts are already what you know how to build (form filling, scraping, file upload, downloads)
# * The WhatsApp bot just triggers them when the user sends a message
# * After the script finishes, you send back the result or Excel file

# **Time needed:** ~2–3 hours to integrate a single automation task

# ---

# # ⭐ **Step 3: Sending results and files**

# * WhatsApp Cloud API lets you send text, buttons, files
# * You just call an API with file path or message
# * That’s it — no UI, no website, no installation

# **Time needed:** ~1 hour to test file sending

# ---

# # ⭐ **Step 4: Secure login handling**

# * Users send username/password once
# * You run PyDoll to log in on your server
# * Extract session cookies
# * Delete raw password
# * All future automation uses session cookies

# **Time needed:** ~1–2 hours to implement securely

# ---

# # ⭐ **Step 5: Combine everything**

# * User sends command → WhatsApp bot receives → triggers PyDoll → executes → sends result
# * You can start **with 1 automation task first** (e.g., extract transactions)
# * Once working, add more tasks later

# **Time needed:** ~1 day to have a simple, fully working bot for 1 worker

# ---

# # ✅ **Key takeaway**

# It *looks* complex because there are many moving parts, but really:

# * Python + PyDoll = backend automation
# * WhatsApp API = simple trigger & response
# * Excel/file handling = standard Python libraries

# You don’t need to learn web development or make a GUI.

# ---

# # ⚡ **Pro tip**

# Start with **one automation task** (like “extract data to Excel”) and make it work fully over WhatsApp. Once it works, you can **scale it to multiple tasks** and multiple workers.

# ---

# If you want, I can **draw the full roadmap for building your WhatsApp automation bot from scratch** — step by step, beginner-friendly, with code snippets for **login, automation, Excel extraction, and file delivery**.

# Do you want me to do that next?






