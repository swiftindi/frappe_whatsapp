"""Webhook."""
import frappe
import json
import requests
import base64


from werkzeug.wrappers import Response


@frappe.whitelist(allow_guest=True)
def webhook():
    """Meta webhook."""
    if frappe.request.method == "GET":
        return get()
    return post()


def get():
    """Get."""
    hub_challenge = frappe.form_dict.get("hub.challenge")
    webhook_verify_token = frappe.db.get_single_value(
        "Whatsapp Settings", "webhook_verify_token"
    )

    if frappe.form_dict.get("hub.verify_token") != webhook_verify_token:
        frappe.throw("Verify token does not match")

    return Response(hub_challenge, status=200)


def post():
    """Post."""
    data = frappe.local.form_dict
    frappe.get_doc({
        "doctype": "WhatsApp Notification Log",
        "template": "Webhook",
        "meta_data": json.dumps(data)
    }).insert(ignore_permissions=True)

    messages = []
    try:
        messages = data["entry"][0]["changes"][0]["value"].get("messages", [])
    except KeyError:
        messages = data["entry"]["changes"][0]["value"].get("messages", [])

    if messages:
        for message in messages:
            message_type = message['type']
            if message_type == 'text':
                frappe.get_doc({
                    "doctype": "WhatsApp Message",
                    "type": "Incoming",
                    "from": customer(message),
                    "message": message['text']['body'],
                    "view": "" # il campo HTML e' vuoto, nessun file multimediale in arrivo
                }).insert(ignore_permissions=True)
            elif message_type in ["image", "audio", "video", "document"]:
                media_id = message[message_type]["id"]
                mime_type = message[message_type]["mime_type"]
                file_extension = mime_type.split('/')[1]  # Ricavo l'estensione del file in arrivo

               # Effettua la richiesta per scaricare il file utilizzando l'ID
                url = f'https://api.whatsapp.com/{message_type}/{media_id}'
                response = requests.get(url)

                if response.status_code == 200:
                 file_data = response.content

                 file_path = "/"  # Sostituisci con il percorso desiderato
                 file_name = f"{frappe.generate_hash(length=10)}.{file_extension}"
                 file_full_path = file_path + file_name

                 with open(file_full_path, "wb") as file:
                  file.write(file_data)
 
                  if message_type == "video":
                   frappe.get_doc({
                     "doctype": "WhatsApp Message",
                     "type": "Incoming",
                     "from": customer(message),
                     "message": f"{message_type} file: {file_name}",
                     "view": '<html><head><title>Player video</title></head><body><video width="640" height="360" controls><source src=' + file_full_path + ' type="video/mp4">Il tuo browser non supporta il tag video.</video></body></html>'
                   }).insert(ignore_permissions=True)

                  elif message_type == "audio":
                   frappe.get_doc({
                     "doctype": "WhatsApp Message",
                     "type": "Incoming",
                     "from": customer(message),
                     "message": f"{message_type} file: {file_name}",
                     "view": '<html><head><title>Player audio</title></head><body><audio controls><source src='+ file_full_path +' type="audio/mp3">Il tuo browser non supporta audio.</audio></body></html>'
                   }).insert(ignore_permissions=True)

                  elif message_type == "image":
                   frappe.get_doc({
                     "doctype": "WhatsApp Message",
                     "type": "Incoming",
                     "from": customer(message),
                     "message": f"{message_type} file: {file_name}",
                     "view": '<html> <head> <style> .image-viewer { display: flex; align-items: center; justify-content: center; height: 100vh; } .image-container { max-width: 100%; max-height: 100%; } .image { max-width: 100%; max-height: 100%; } </style> </head> <body> <div class="image-viewer"> <div class="image-container"> <img class="image" src=' + file_full_path + ' alt="Image"> </div> </div> </body> </html>'
                   }).insert(ignore_permissions=True)

                  elif message_type == "document":
                   frappe.get_doc({
                     "doctype": "WhatsApp Message",
                     "type": "Incoming",
                     "from": customer(message),
                     "message": f"{message_type} file: {file_name}",
                     "view": '<html> <head> <title>Visualizzatore di ocumenti</title> <style> #document-viewer { width: 100%; height: 600px; } </style> </head> <body> <div id="document-viewer"> <iframe src=' + file_full_path + ' width="100%" height="100%"></iframe> </div> </body> </html>'
                   }).insert(ignore_permissions=True)
    else:
        changes = None
        try:
            changes = data["entry"][0]["changes"][0]
        except KeyError:
            changes = data["entry"]["changes"][0]
        update_status(changes)
    return

def customer(message):
    if (frappe.db.get_value("Customer", filters={"mobile_no": ("+" + str(message['from']))}, fieldname="customer_name")):
        return frappe.db.get_value("Customer", filters={"mobile_no": ("+" + str(message['from']))}, fieldname="customer_name")

    else:
        return "non registrato: " + "+" + str(message['from'])
    

def update_status(data):
    """Update status hook."""
    if data.get("field") == "message_template_status_update":
        update_template_status(data['value'])

    elif data.get("field") == "messages":
        update_message_status(data['value'])


def update_template_status(data):
    """Update template status."""
    frappe.db.sql(
        """UPDATE `tabWhatsApp Templates`
        SET status = %(event)s
        WHERE id = %(message_template_id)s""",
        data
    )


def update_message_status(data):
    """Update message status."""
    id = data['statuses'][0]['id']
    status = data['statuses'][0]['status']
    conversation = data['statuses'][0].get('conversation', {}).get('id')
    name = frappe.db.get_value("WhatsApp Message", filters={"message_id": id})
    doc = frappe.get_doc("WhatsApp Message", name)

    doc.status = status
    if conversation:
        doc.conversation_id = conversation
    doc.save(ignore_permissions=True)

import requests

def send_message_to_whatsapp_message(message):
    """Send message to WhatsApp Message."""
    url = "https://ced.confcommercioimola.cloud/api/method/frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_message.whatsapp_message.receive" 
    data = {
        "messaging_product": "whatsapp",
        "to": message['from'],
        "type": "incoming",
        "message": message['text']['body']
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        frappe.msgprint("Message sent to WhatsApp Message successfully!")
    except requests.exceptions.RequestException as e:
        frappe.log_error("Error sending message to WhatsApp Message: {}".format(str(e)))
