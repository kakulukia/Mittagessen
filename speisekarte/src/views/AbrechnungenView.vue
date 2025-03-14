<template lang="pug">
  .container
    v-btn.auslieferung(icon href="lieferungen")
      v-icon mdi-truck-fast

    h1(v-if="!selectedCustomer") Kundenübersicht
    .overview(v-if="selectedCustomer")
      v-row
        .col
          h1 {{ selectedCustomer.name }}
            v-btn(@click="resetView()" icon)
              v-icon mdi-close
        .col-auto
          v-btn-toggle(dense borderless)
            v-btn(@click="showInvoices = false")
              v-icon mdi-calendar-blank
            v-btn(@click="loadInvoices()")
              v-icon mdi-invoice-text-clock-outline
            v-btn(@click="generateNewInvoice()")
              v-icon mdi-invoice-text-plus-outline
      .invoices(v-if="showInvoices")
        div Rechnungen
        br
        div(v-if="invoices.length === 0") Keine Rechnungen vorhanden
        v-list(v-if="invoices.length !== 0")
          v-list-item(v-for="invoice in invoices" :key="invoice.id")
            v-list-item-content
              v-list-item-title {{ invoice.date }}
              v-list-item-subtitle {{ invoice.total }} €
            v-list-item-action
              v-btn-toggle(dense borderless)
                v-btn
                  a(:href="`${apiHost}/api/invoices/${invoice.id}/pdf/`" target="_blank")
                    v-icon mdi-file-download-outline

      .days(v-if="!showInvoices")
        div Tagesübersicht
        br

        day-meal-editor(v-for="day in days" :day="day" :customer="selectedCustomer" @update="loadInvoiceDays" :key="day.id")

        br
        v-btn-toggle(dense borderless)
          v-btn(@click="createNewDay()" v-if="!newDay.date") +

        day-meal-editor(
          v-if="newDay.date"
          :day="newDay"
          :customer="selectedCustomer"
          @new-day-created="newDayCreated()"
          :blockedTimes="blockedTimes"
          @update="loadInvoiceDays()"
        )


    .customers(v-if="!editCustomer && !selectedCustomer")

      v-row(align="center")
        .col
          v-text-field(label="Suche" v-model="search" append-icon="mdi-magnify" clearable)
        .col-auto
          v-btn-toggle(dense borderless)
            v-btn(@click="create") Neu

      v-list.customerList
        v-list-item.customer(v-for="customer in filteredCustomers" :key="customer.id")
          v-list-item-icon.pointer(@click="selectCustomer(customer)")
            v-icon(v-if="customer.delivery_type === 'delivery'") mdi-truck-delivery-outline
            v-icon(v-if="customer.delivery_type === 'takeaway'") mdi-food-takeout-box-outline
          v-list-item-content.pointer(@click="selectCustomer(customer)")
            v-list-item-title {{ customer.name }}
            v-list-item-subtitle {{ customer.short_address }}
          v-list-item-action
            v-btn-toggle(dense borderless)
              v-btn(@click="setCustomer(customer)" @clicik.stop="true")
                v-icon mdi-pencil


    .newCustomer(v-if="editCustomer")
      h4(v-if="!newCustomer.id") Neuen Kunden anlegen
      h4(v-if="newCustomer.id") Kunden bearbeiten
      br
      br

      v-textarea(label="Adresse" rows="4" v-model="newCustomer.address")
      v-text-field(label="eMail" v-model="newCustomer.email")
      // wee need radio otion for delivery type
      v-radio-group(inline v-model="newCustomer.delivery_type")
        v-radio(label="Belieferung" value="delivery")
        v-radio(label="Selbstabholer" value="takeaway")
      v-row
        .col-auto
          v-btn(@click="saveCustomer") Speichern
        .col-auto
          v-btn(@click="editCustomer = false") Abbrechen

</template>

<script>
import DayMealEditor from '@/components/DayMealEditor';

export default {
  name: 'AbrechnungenView',
  inject: ['apiHost'],
  components: {
    DayMealEditor,
  },
  data () {
      return {
        editCustomer: false,
        newCustomer: {
          address: '',
          email: '',
          delivery_type: '',
        },
        customers: [],
        selectedCustomer: null,
        search : '',
        days: [],
        newDay: {
          date: '',
          delivered: false,
          combining_dates: false,
        },
        toggle_exclusive: 2,
        showInvoices: false,
        invoices: [],
      }
    },

  created () {
     this.loadCustomers()
  },
  methods: {
    generateNewInvoice() {
      this.axios.get(`/customers/${this.selectedCustomer.id}/generate-invoice/`)
        .then((response) => {
          let invoice_id = response.data.invoice_id
          window.open(`${this.apiHost}/api/invoices/${invoice_id}/pdf/`, '_blank')
          this.loadInvoiceDays()
        }).catch((error) => {
          let message = error.response.data.message
          alert(message)
        });
    },
    setCustomer(customer) {
      this.newCustomer = customer
      this.editCustomer = true
    },
    resetView() {
      this.selectedCustomer = null
      this.showInvoices = false
      this.newDay = {
        date: '',
        delivered: false,
        combining_dates: false,
      }
    },
    loadInvoices() {
      this.showInvoices = true
      this.axios.get(`/customers/${this.selectedCustomer.id}/invoices/`)
        .then(response => {
          this.invoices = response.data
        })
    },
    selectCustomer(customer) {
      this.selectedCustomer = customer
      this.loadInvoiceDays()
    },
    loadInvoiceDays() {
      this.axios.get(`/customers/${this.selectedCustomer.id}/invoice-days/`)
        .then(response => {
          let days = response.data;

          // convert all dates to Date objects
          days.forEach(day => {
            day.date = new Date(day.date)
          })
          this.days = days

        })
        .catch(error => {
          console.error("Fehler beim Laden der Invoice Days:", error);
        });
    },
    create() {
      this.editCustomer = true
      this.newCustomer = {
        address: '',
        email: '',
        deliveryType: '',
      }
    },
    createNewDay() {
      this.loadInvoiceDays()
      this.newDay = {
        date: new Date(),
        delivered: false,
        combining_dates: false,
      }

      // check if days contains the current date
      // while this is true add a day to the date
      while (this.days.find(day => day.date.toISODate() === this.newDay.date.toISODate())) {
        this.newDay.date.setDate(this.newDay.date.getDate() + 1);
      }


    },
    newDayCreated() {
      console.log("newDayCreated")
      this.newDay = {
        date: '',
        delivered: false,
        combining_dates: false,
      }
      this.loadInvoiceDays()
    },
    resetCustomer() {
      this.editCustomer = false
      this.newCustomer = {
        address: '',
        email: '',
        deliveryType: '',
      }
    },
    saveCustomer() {
      if (this.newCustomer.id) {
        this.axios.put(`customers/${this.newCustomer.id}/`, this.newCustomer)
          .then(() => {
            this.resetCustomer()
            this.loadCustomers()
          })
      } else {
        this.axios.post('customers/', this.newCustomer)
          .then(() => {
            this.resetCustomer()
            this.loadCustomers()
          })
      }
    },
    loadCustomers() {
      this.axios.get('customers/', ).then((response) => {
         this.customers = response.data
     })
    },
  },
  computed: {
    filteredCustomers() {
      if (this.search === "") {
        return this.customers
      }
      // Return filtered customers based on search input
      return this.customers.filter(customer =>
        customer.name.toLowerCase().includes(this.search.toLowerCase())
      );
    },
    blockedTimes() {
      if (!this.days) return []
      return this.days.map(day => {
        const d = new Date(day.date);
        return day.combining_dates ? d.toISOMonth() : d.toISODate()
      });
    }
  },
};
</script>

<style scoped lang="sass">
.v-btn.delivery
  color: lightgray
  &.delivered
    color: green
.customer:hover
  background-color: #f0f0f0

.pointer
  cursor: pointer

.auslieferung
  position: fixed
  bottom: 50px
  right: 50px
  .v-icon
    font-size: 50px

</style>
