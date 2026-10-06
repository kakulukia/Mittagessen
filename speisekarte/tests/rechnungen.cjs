const assert = require('assert')
const fs = require('fs')
const path = require('path')
const vm = require('vm')
const source = fs.readFileSync(path.join(__dirname, '../src/views/RechnungenView.vue'), 'utf8')
const component = vm.runInNewContext(source.match(/<script>([\s\S]*?)<\/script>/)[1].replace('export default', 'module.exports ='), { module: {} })
const view = component.data()
for (const [name, method] of Object.entries(component.methods)) view[name] = method.bind(view)
for (const [name, getter] of Object.entries(component.computed)) Object.defineProperty(view, name, { get: getter.bind(view) })
const invoice = (customer, month, net, tax, total) => ({ customer_name: customer, delivery_months: month, net, tax, total })
view.invoices = [
  invoice('Müller GmbH', ['2026-09'], '0.10', '0.01', '0.11'),
  invoice('Anderer Kunde', ['2026-09'], '0.20', '0.01', '0.21'),
  invoice('Müller GmbH', ['2025-09'], '100.00', '7.00', '107.00'),
  invoice('Ohne Lieferungen', [], '1.00', '0.07', '1.07'),
  invoice('Mehrere Monate', ['2026-08', '2026-09'], '2.00', '0.14', '2.14'),
]
view.selectedMonth = '2026-09'
assert.equal(view.monthInvoices.length, 2)
assert.equal(view.totals.net, 0.30)
assert.equal(view.totals.total, 0.32)
assert.equal(view.availableMonths.join(','), '2026-09,2025-09')
view.search = '  MÜLLER  '
assert.equal(view.filteredInvoices.length, 1)
assert.equal(view.totals.net, 0.10)
assert.equal(view.totals.tax, 0.01)
assert.equal(view.totals.total, 0.11)
view.selectedMonth = ''
assert.equal(view.filteredInvoices.length, 2)
assert.equal(view.totals.net, 100.10)
assert.equal(view.totals.tax, 7.01)
assert.equal(view.totals.total, 107.11)
view.invoices[1].total = null
assert.equal(view.totals.total, 107.11)
view.invoices[1].total = '0.21'
view.selectedMonth = '2026-09'
view.search = '<script>不存在'
assert.equal(view.filteredInvoices.length, 0)
assert.equal(view.totals.net, 0)
assert.equal(view.totals.tax, 0)
assert.equal(view.totals.total, 0)
view.search = null
assert.equal(view.filteredInvoices.length, 2)
view.selectedMonth = '2026-10'
assert.equal(view.filteredInvoices.length, 0)
assert.equal(view.totals.total, 0)
view.selectedMonth = 'unassigned'
assert.equal(view.filteredInvoices.length, 2)
assert.equal(view.unassignedCount, 2)
view.selectedMonth = ''
assert.equal(view.filteredInvoices.length, 5)
view.invoices[0].total = null
assert.equal(view.totals.total, null)
assert.equal(view.formatAmount(null), 'Unvollständig')
view.invoices[0].total = 'invalid'
assert.equal(view.totals.total, null)
view.invoices = []
assert.equal(view.filteredInvoices.length, 0)
assert.equal(view.totals.total, 0)
assert.equal(view.formatAmount(0), '0,00 €')
assert.equal(view.pageCount, 0)
assert.equal(view.paginatedInvoices.length, 0)

view.invoices = Array.from({ length: 45 }, (_, index) => ({
  ...invoice(index === 44 ? 'Gesuchter Kunde' : 'Anderer Kunde', ['2026-09'], '10.00', '0.70', '10.70'),
  id: index + 1,
}))
assert.equal(view.pageCount, 3)
assert.equal(view.paginatedInvoices.length, 20)
view.page = 2
assert.equal(view.paginatedInvoices[0].id, 21)
assert.equal(view.paginatedInvoices.length, 20)
assert.equal(view.totals.total, 481.50)
view.page = 3
assert.equal(view.paginatedInvoices.length, 5)
assert.equal(view.paginatedInvoices[0].id, 41)
view.search = 'Anderer Kunde'
component.watch.filteredInvoices.call(view)
assert.equal(view.pageCount, 3)
assert.equal(view.totals.total, 470.80)
view.page = 3
assert.equal(view.paginatedInvoices.length, 4)
assert.equal(view.totals.total, 470.80)
view.search = 'Gesuchter Kunde'
component.watch.filteredInvoices.call(view)
assert.equal(view.page, 1)
assert.equal(view.pageCount, 1)
assert.equal(view.paginatedInvoices[0].id, 45)
assert.equal(view.totals.total, 10.70)
view.search = ''

;(async () => {
  view.axios = { get: async () => { throw new Error('offline') } }
  await view.loadInvoices()
  assert.equal(view.loading, false)
  assert.equal(view.error, true)
  view.axios = { get: async () => ({ data: [invoice('Kunde', ['2026-09'], '100.00', '7.00', '107.00')] }) }
  await view.loadInvoices()
  assert.equal(view.error, false)
  assert.equal(view.selectedMonth, '2026-09')
  console.log('Rechnungsübersicht: Monatszuordnung, Suche, Cent-Summen und Ladefehler geprüft.')
})().catch(error => { console.error(error); process.exitCode = 1 })
