const express = require('express');
const router = express.Router();
const reportController = require('../controllers/reportController');

// Ruta para generar el reporte de facturas
// Route to generate the invoice report
router.get('/invoices/report', reportController.generateInvoiceReport);

module.exports = router;