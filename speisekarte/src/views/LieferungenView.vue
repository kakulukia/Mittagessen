<template lang="pug">
  .container
    h1 Anstehende Lieferungen für {{ new Date() | moment('dddd') }} den {{ new Date() | moment('DD.MM.YYYY') }}

    div(v-if="invoiceDays.length === 0") Heute keine Lieferungen vorhanden
    div(v-if="invoiceDays.length !== 0")
      div {{ invoiceDays.length }} Kunde
        span(v-if="invoiceDays.length > 1") n
      v-list
        v-list-item.mt-4(v-for="invoiceDay in invoiceDays" :key="invoiceDay.id")
          v-list-item-content
            v-list-item-title
              strong {{ invoiceDay.customer.name }}
            v-list-item-subtitle {{ invoiceDay.customer.short_address }}

            v-btn-toggle.delivery(dense borderless)
              v-btn(
                :color="invoiceDay.delivered ? 'success' : 'default'"
                :class="{delivered: invoiceDay.delivered}"
                @click="toggleDelivered(invoiceDay)") ✓

            div.mt-4
              div(v-for="meal in invoiceDay.meals" :key="meal.id")
                div.meals
                  span.text-right {{ meal.count }}x
                  span {{ meal.name }}
                div.meals(v-if="meal.comment")
                  span.text-right
                    strong Extra
                  span {{ meal.comment }}
          v-list-item-action
</template>

<script>
export default {
  name: 'LieferungenView',
  inject: ['apiHost'],
  data () {
      return {
        invoiceDays: [],
      }
    },

  created () {
     this.loadInvoiceDays()
  },
  methods: {
    toggleDelivered(day) {
      console.log(day)
      // Wenn der Tag auf delivered gesetz
      day.delivered = !day.delivered
      this.axios.patch(`invoice-days/${day.id}/`, { delivered: day.delivered }).then(() => {
      }).catch(() => {
        day.delivered = !day.delivered
      })
    },
    loadInvoiceDays() {
      this.axios.get(`/invoice-days/today/`)
        .then(response => {
          this.invoiceDays = response.data;
        })
    },
  },
  computed: {
  },
};
</script>

<style scoped lang="sass">
.meals
  display: grid
  grid-template-columns: 40px 1fr
  grid-gap: 10px

.delivery
  position: absolute
  top: 12px
  right: 0
  //.delivered
    color: green

</style>
