import requests
import binascii
import logging
import xml.etree.ElementTree as etree
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.spain_gls_shipping_integration.models.gls_spain_response import Response

_logger = logging.getLogger(__name__)


class GlsShipping(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("gls_spain", "GLS Spain")], ondelete={'gls_spain': 'set default'})
    spain_gls_service = fields.Selection([("1", "1 Courier"),
                                          ("37", "37 Economy"),
                                          ("74", "74 EuroBusinessParcel"),
                                          ("12", "12 International Express"),
                                          ("13", "13 International Economy")], string="GLS Service", help="Select GLS "
                                                                                                        "Service")

    spain_gls_api_schedule = fields.Selection([("3", '3 ASM24'),
                                               ("2", '2 ASM14'),
                                               ("18", '18 Economy'),
                                               ("19", '19 ParcelShop')], string="GLS Schedule", help="Select Gls Schedule")


    def gls_spain_rate_shipment(self, order):
        return {'success': True, 'price': 0.0, 'error_message': False, 'warning_message': False}

    def gls_spain_label_request_data(self, pickings=False):
        """
        All Require Data For Creating Label
        :param pickings:
        :return: Request Data For Creating New Label
        """
        sender_id = pickings.picking_type_id and pickings.picking_type_id.warehouse_id and \
                    pickings.picking_type_id.warehouse_id.partner_id

        receiver_id = pickings.partner_id
        spain_gls_userid = self.company_id and self.company_id.spain_gls_userid

        # check sender Country
        if not sender_id.zip or not sender_id.city or not sender_id.country_id:
            raise ValidationError("Please Define Proper Sender Address!")

        # check Receiver Country
        if not receiver_id.zip or not receiver_id.city or not receiver_id.country_id:
            raise ValidationError("Please Define Proper Recipient Address!")

        # check Recevier Phone
        if not receiver_id.phone:
            raise ValidationError("Please Define Recevier Phone Number!")

        master_node = etree.Element('soap12:Envelope')
        master_node.attrib['xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
        master_node.attrib['xmlns:xsd'] = "http://www.w3.org/2001/XMLSchema"
        master_node.attrib['xmlns:soap12'] = "http://www.w3.org/2003/05/soap-envelope"

        sub_master_node_soap_body = etree.SubElement(master_node, 'soap12:Body')
        sub_master_node_grab_serivcious = etree.SubElement(sub_master_node_soap_body, 'GrabaServicios')
        sub_master_node_grab_serivcious.attrib['xmlns'] = 'http://www.asmred.com/'
        sub_master_node_docin = etree.SubElement(sub_master_node_grab_serivcious, 'docIn')
        sub_master_node_servicios = etree.SubElement(sub_master_node_docin, 'Servicios')
        sub_master_node_servicios.attrib['uidcliente'] = "{}".format(spain_gls_userid)
        sub_master_node_servicios.attrib['xmlns'] = "http://www.asmred.com/"
        sub_master_node_envio = etree.SubElement(sub_master_node_servicios, 'Envio')
        sub_master_node_envio.attrib['codbarras'] = ""

        # sale Order Information
        etree.SubElement(sub_master_node_envio, 'Fecha').text = "{}".format(self.create_date.strftime("%d/%m/%Y"))
        etree.SubElement(sub_master_node_envio, 'Servicio').text = "{}".format(self.spain_gls_service)
        etree.SubElement(sub_master_node_envio, 'Horario').text = "{}".format(self.spain_gls_api_schedule)
        etree.SubElement(sub_master_node_envio, 'Bultos').text = "{}".format(1)  # How Many Label You Want To print
        etree.SubElement(sub_master_node_envio, 'Peso').text = "{}".format(pickings.shipping_weight)  # package
        # weight in Kg

        # Sender Information
        root_node_Remite = etree.SubElement(sub_master_node_envio, 'Remite')
        etree.SubElement(root_node_Remite, 'Nombre').text = "{}".format(sender_id.name)
        etree.SubElement(root_node_Remite, 'Direccion').text = "{}".format(sender_id.street)
        etree.SubElement(root_node_Remite, 'Poblacion').text = "{}".format(sender_id.city)
        etree.SubElement(root_node_Remite, 'Pais').text = "{}".format(sender_id.country_id.phone_code)
        etree.SubElement(root_node_Remite, 'CP').text = "{}".format(sender_id.zip)
        etree.SubElement(root_node_Remite, 'Movil').text = "{}".format(sender_id.phone)
        etree.SubElement(root_node_Remite, 'Email').text = "{}".format(sender_id.email)

        # Recevier Information
        root_node_Destinatario = etree.SubElement(sub_master_node_envio, 'Destinatario')
        etree.SubElement(root_node_Destinatario, 'Nombre').text = "{}".format(receiver_id.name)
        etree.SubElement(root_node_Destinatario, 'Direccion').text = "{}".format(receiver_id.street)
        etree.SubElement(root_node_Destinatario, 'Poblacion').text = "{}".format(receiver_id.city)
        etree.SubElement(root_node_Destinatario, 'CP').text = "{}".format(receiver_id.zip)
        etree.SubElement(root_node_Destinatario, 'Pais').text = "{}".format(receiver_id.country_id.phone_code)
        etree.SubElement(root_node_Destinatario, 'Movil').text = "{}".format(receiver_id.phone)
        etree.SubElement(root_node_Destinatario, 'Email').text = "{}".format(receiver_id.email)

        root_node_Referencias = etree.SubElement(sub_master_node_envio, 'Referencias')
        etree.SubElement(root_node_Referencias, 'Referencia').attrib['tipo'] = "C"
        etree.SubElement(root_node_Referencias, 'Referencia').text = "{}".format(pickings.name)

        root_node_DevuelveAdicionales = etree.SubElement(sub_master_node_envio, 'DevuelveAdicionales')
        etree.SubElement(root_node_DevuelveAdicionales, 'Etiqueta').attrib['tipo'] = "PDF"
        return etree.tostring(master_node)

    @api.model
    def gls_spain_send_shipping(self, pickings):
        """
        This Method Send Request To GSl And Retuen Label And Price
        :param pickings:
        :return: Tracking Number and Cost
        """
        if not self.company_id:
            raise ValidationError("Company Not Selected In Delivery Method!")
        spain_gls_api_url = self.company_id and self.company_id.spain_gls_api_url
        request_data = self.gls_spain_label_request_data(pickings)
        headers = {'Content-Type': 'application/soap+xml; charset=UTF-8'}
        try:
            _logger.info("POST Request To {}".format(spain_gls_api_url))
            request = requests.post(url=spain_gls_api_url, data=request_data, headers=headers)
        except Exception as e:
            raise ValidationError(e)
        if request.status_code != 200:
            raise ValidationError("Label Request Data Invalid  {}".format(request.content))
        api = Response(request)
        result = api.dict()
        result_envelope = result.get('Envelope').get('Body').get('GrabaServiciosResponse').get(
            'GrabaServiciosResult').get('Servicios').get('Envio')
        if not result_envelope:
            raise ValidationError("Lable Not Found In Response {}".format(result))
        if not result_envelope.get('Etiquetas'):
            raise ValidationError("Lable Not Found In Response {}".format(result_envelope))
        binary_data = result_envelope.get('Etiquetas').get('Etiqueta').get('value')
        binary_data = binascii.a2b_base64(str(binary_data))
        # tracking_id = result_envelope.get('Referencias').get('Referencia')[2].get('value')
        tracking_id = result_envelope.get('_codbarras')
        message = ("Label created!<br/> <b>Label Tracking Number : </b>%s<br/> " % (
            tracking_id))
        pickings.message_post(body=message, attachments=[
            ('Label-%s.%s' % (tracking_id, "pdf"), binary_data)])
        delivery_price = sum(pickings.sale_id and pickings.sale_id.order_line.filtered(lambda line:line.is_delivery).mapped('price_unit'))
        return [{
            'exact_price': delivery_price or 0.0,
            'tracking_number': tracking_id}]

    def gls_spain_cancel_shipment(self, pickings):
        raise ValidationError("Cancel is not possible in GLS Spain!")


    def gls_spain_get_tracking_link(self, picking):
        receiver_id = picking.partner_id
        # return 'https://m.gls-spain.es/%s' % (picking.carrier_tracking_ref)
        return 'https://m.gls-spain.es/e/%s/%s' % (picking.carrier_tracking_ref,receiver_id.zip)
