const PDFDocument = require('pdfkit');
const fs = require('fs');
const path = require('path');
const Invoice = require('../models/Invoice');

// Generar reporte de facturas en PDF
// Generate invoice report in PDF
exports.generateInvoiceReport = async (req, res) => {
    try {
        // Obtener todas las facturas en la base de datos
        // Get all invoices in the database
        const invoices = await Invoice.findAll();

        // Crear un nuevo documento PDF
        // Create a new PDF document
        const doc = new PDFDocument();

        // Ruta de guardado PDF
        // PDF save path
        const filePath = path.join(__dirname, '../reports', 'invoices_report.pdf');

        // Guardar el PDF en un archivo
        // Save the PDF to a file
        doc.pipe(fs.createWriteStream(filePath));

        // Título del documento
        // Document title
        doc.fontSize(18).text('Reporte de Facturas', { aling: 'center'});
        doc.moveDown(2);

        // Añadir datos a la factura
        // Add data to the invoice
        invoices.forEach((invoice, index) => {
            doc.fontSize(12).text(`Factura #${invoice.id}`, { aling: 'left'});
            doc.text(`Cliente: ${invoice.clientName}`);
            doc.text(`Monto: ${invoice.totalAmount}`);
            doc.text(`Fecha: ${invoice.date}`);
            doc.moveDown(1);
        });

        // Finalizar el documento PDF
        // Finalize the PDF document
        doc.end();

        // Enviar el archivo como respuesta
        // Send file as response
        res.download(filePath);
    } catch (error) {
        console.error('Error generando el reporte de facturas:', error);
        res.status(500).json({ message: 'Error al generar reporte.' });
    }
};