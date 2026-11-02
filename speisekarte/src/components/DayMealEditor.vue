<template lang="pug">
  .day(v-if="day.date")
    v-row.dayDisplay(align="center" dense)
      .col
        strong {{ formattedDate }}
      .col-auto
        v-btn-toggle(dense borderless v-if="!day.id")
          v-btn(@click="subtractFromDay")
            v-icon mdi-chevron-up
          v-btn(@click="addToDay")
            v-icon mdi-chevron-down
      .col-auto
        v-btn(
          v-if="day.id"
          :color="day.reviewed ? 'green darken-3' : 'deep-orange darken-4'"
          outlined
          :title="day.reviewed ? 'Prüfung zurücknehmen' : 'Bestellung als geprüft markieren'"
          :disabled="!canReview"
          :aria-pressed="day.reviewed ? 'true' : 'false'"
          @click="updateDay({ reviewed: !day.reviewed })"
        )
          v-icon(left) {{ day.reviewed ? 'mdi-check-circle-outline' : 'mdi-clipboard-check-outline' }}
          | {{ day.reviewed ? 'Geprüft' : 'Ungeprüft' }}
      .col-auto
        v-btn-toggle(dense borderless)
          v-btn(
            v-if="!day.id"
            :color="day.combining_dates ? 'primary' : 'default'"
            @click="toggleCombiningDates(day)"
          )
            v-icon mdi-calendar-month-outline
          v-btn.delivery(
            v-if="showDelivery && day.id && day.date < new Date()"
            :class="{delivered: day.delivered}"
            @click="toggleDelivered" :color="day.delivered ? 'success' : 'error'") ✓

    v-alert.mt-3(v-if="saveError" type="error" dense role="alert") {{ saveError }}
    v-expansion-panels.mt-3(v-if="day.id" flat)
      v-expansion-panel
        v-expansion-panel-header Originalnachricht{{ day.source_message ? '' : ' hinzufügen' }}
        v-expansion-panel-content
          v-textarea(
            v-model="sourceMessage"
            label="Originalnachricht"
            placeholder="WhatsApp-Nachricht hier einfügen"
            rows="3"
            auto-grow
            outlined
            hide-details
          )
          v-btn.mt-3(
            :disabled="pendingRequests > 0 || sourceMessage === (day.source_message || '')"
            @click="updateDay({ source_message: sourceMessage })"
          ) Nachricht speichern

    // show existing meals
    div(v-for="meal in day.meals" :key="meal.id")
      v-row.meals(align="center" dense :class="{withComment: meal.showComment}")
        .col
          v-combobox(
            v-model="meal.name"
            :items="mealItems"
            label="Gericht"
            clearable
            hide-details
            @change="updateMeal(meal)"
          )
        .col-auto
          v-btn-toggle(dense borderless)
            v-btn(@click="meal.showComment = !meal.showComment" :color="meal.comment ? 'yellow' : 'default'")
              v-icon mdi-comment-alert-outline
        .col-2
          v-combobox(
            v-model="meal.count"
            :items="countItems"
            label="Anzahl"
            type="number"
            min="1"
            hide-details
            @change="updateMeal(meal)"
          )
        .col-2
          v-text-field(
            v-model="meal.price"
            label="Preis"
            type="number"
            step="0.50"
            :suffix="meal.price_needs_review ? '' : '€'"
            @blur="updateMeal(meal)"
            hide-details
          )
            template(v-if="meal.price_needs_review" v-slot:append)
              span.red--text.text--darken-4.font-weight-bold(title="Preis prüfen" role="img" aria-label="Preis prüfen") €?
      v-expand-transition
        v-row.withComment.comment(align="center" dense v-if="meal.showComment")
          .col
            v-text-field(
              v-model="meal.comment"
              label="Änderungswünsche"
              hide-details
              @blur="updateMeal(meal)"
            )


    // add option to add a new meal
    v-row(align="center" dense)
      .col
        v-combobox(
          v-model="newMeal.name"
          :items="mealItems"
          label="Neues Gericht"
          clearable
          hide-details
          dense
          @blur="updateMeal(newMeal)"
        )
      .col-2
        v-combobox(
          v-model="newMeal.count"
          :items="countItems"
          label="Anzahl"
          type="number"
          min="1"
          dense
          hide-details
          @blur="updateMeal(newMeal)"
        )
      .col-2
        v-text-field(
          v-model="newMeal.price"
          label="Preis"
          type="number"
          min="0"
          step="0.50"
          suffix="€"
          @blur="updateMeal(newMeal)"
        )

    v-btn-toggle.loadPlans(dense borderless v-if="!plannedDay && !day.combining_dates &&!isWeekend")
      v-btn(@click="loadPlan")
        v-icon mdi-silverware-variant
    .plannedDay(v-if="plannedDay && !day.combining_dates")
      div
        strong Geplanter Tag
      div(v-if="plannedDay.plans.length === 0")
        p Noch kein Plan vorhanden
      div.plannedMeal(v-for="plan in plannedDay.plans" :key="plan.id")
        span.pointer(@click="newMealFromPlan(plan)") {{ plan.meal.name }}

</template>

<script>
export default {
  name: 'DayMealEditor',
  props: {
    showDelivery: {
      type: Boolean,
      default: true
    },
    // Der Tag, der entweder neu (ohne id) oder bereits bestehend ist
    day: {
      type: Object,
      required: true
    },
    // Aktuell ausgewählter Kunde
    customer: {
      type: Object,
      required: true
    },
    blockedTimes: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      newMeal: {
        name: '',
        count: 1,
        price: '',
        delivered: false,
        // day wird später gesetzt via: this.newMeal.day = this.day.id
      },
      mealItems: ['Mittagessen', 'Mittagessen 2', 'Eintopf', 'Nachtisch'],
      countItems: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      plannedDay: undefined,
      planTimer: undefined,
      sourceMessage: this.day.source_message || '',
      pendingRequests: 0,
      saveError: '',
    }
  },
  computed: {
    canReview() {
      return this.pendingRequests === 0 && !this.saveError && this.sourceMessage === (this.day.source_message || '')
    },
    // Computed, um zu gewährleisten, dass wenn day.delivered gesetzt wird,
    // alle Meals (und newMeal) ebenfalls delivered true haben
    allMealsDelivered: {
      get() {
        return this.day.delivered;
      },
      set(val) {
        // Setze delivered beim Tag
        this.day.delivered = val;
        // Falls bereits eine Liste von Meals vorhanden ist, aktualisiere diese
        if (this.day.meals && this.day.meals.length) {
          this.day.meals.forEach(meal => {
            meal.delivered = val;
            this.updateMeal(meal);
          });
        }
      }
    },
    formattedDate() {
      // if this.day.date is a string, return ''
      if (typeof this.day.date === 'string') return ''
      if (!this.day.combining_dates) {
        return this.day.date.toLocaleDateString('de-DE', {
          weekday: 'short',
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        })
      } else {
        return this.day.date.toLocaleDateString('de-DE', {
          year: 'numeric',
          month: 'long',
        })
      }
    },
    isWeekend() {
      return this.day.date.getDay() === 0 || this.day.date.getDay() === 6
    }
  },
  watch: {
    canReview: {
      immediate: true,
      handler(value) {
        this.$emit('review-availability', value)
      }
    }
  },
  methods: {
    newMealFromPlan(plan) {
      let name = plan.meal.name
      if (name.startsWith('- ')) {
        name = 'Schnitzel ' + name.replace('- ', '')
      }
      if (this.newMeal.name === name) {
        this.newMeal.count += 1
      } else {
        this.newMeal = {
          name: name,
          count: 1,
          price: plan.price,
          delivered: false,
        }
      }
      clearTimeout(this.planTimer)
      this.planTimer = setTimeout(() => { this.updateMeal(this.newMeal) }, 1000)
    },
    deleteDay() {
      this.axios.delete(`invoice-days/${this.day.id}/`)
        .then(() => {
          // Optional: Emitte ein Event, wenn ein Tag gelöscht wurde
          this.$emit('update');
        })
        .catch(error => {
          console.error("Fehler beim Löschen des Tages:", error);
        });
    },
    async updateMeal(meal) {
      if (!meal.id && (!meal.name || meal.price === '' || meal.price == null)) return
      // Ignore a second blur while a new position is being created.
      if (!meal.id && this.pendingRequests) return
      this.pendingRequests++
      this.saveError = ''
      try {
        if (!this.day.id) {
          const response = await this.axios.post('invoice-days/', {
            ...this.day,
            customer: this.customer.id,
            date: this.day.date.toISODate(),
          })
          this.$set(this.day, 'id', response.data.id)
          this.$set(this.day, 'source_message', response.data.source_message)
        }
        meal.day = this.day.id
        if (meal.id && meal.count == 0) {
          await this.axios.delete(`invoice-meals/${meal.id}/`)
          if (this.day.meals.length === 1) {
            this.deleteDay()
            return
          }
          this.loadMeals()
        } else if (meal.id) {
          await this.axios.patch(`invoice-meals/${meal.id}/`, meal)
        } else {
          await this.axios.post('invoice-meals/', meal)
          this.newMeal = { name: '', count: 1, price: '', delivered: false }
          this.loadMeals()
          this.$emit('new-day-created')
        }
        const response = await this.axios.get(`invoice-days/${this.day.id}/`)
        this.$set(this.day, 'reviewed', response.data.reviewed)
        const savedMeal = response.data.meals.find(saved => saved.id === meal.id)
        if (savedMeal) this.$set(meal, 'price_needs_review', savedMeal.price_needs_review)
      } catch (error) {
        this.showSaveError(error)
      } finally {
        this.pendingRequests--
      }
    },
    showSaveError(error) {
      const data = error.response && error.response.data
      const messages = data && typeof data === 'object' ? Object.values(data).flat().join(' ') : ''
      this.saveError = messages || 'Speichern fehlgeschlagen. Bitte erneut versuchen.'
    },
    async updateDay(changes) {
      this.pendingRequests++
      this.saveError = ''
      try {
        const response = await this.axios.patch(`invoice-days/${this.day.id}/`, changes)
        this.$set(this.day, 'source_message', response.data.source_message)
        this.sourceMessage = response.data.source_message
        this.$set(this.day, 'reviewed', response.data.reviewed)
        this.day.meals.forEach(meal => {
          const savedMeal = response.data.meals.find(saved => saved.id === meal.id)
          if (savedMeal) this.$set(meal, 'price_needs_review', savedMeal.price_needs_review)
        })
      } catch (error) {
        this.showSaveError(error)
      } finally {
        this.pendingRequests--
      }
    },
    loadMeals() {
      this.axios.get(`invoice-days/${this.day.id}/meals/`)
        .then(response => {
          this.$set(this.day, 'meals', response.data);
        })
    },
    // addToDay und subtractFromDay werden nur im Template aufrufbar, wenn day noch keine id hat
    addToDay() {
      let newDate = new Date(this.day.date)
      if (this.day.combining_dates) {
        newDate.setMonth(newDate.getMonth() + 1)
      } else {
        newDate.setDate(newDate.getDate() + 1)
      }
      this.day.date = this.checkDate(newDate)
    },
    subtractFromDay() {
      let newDate = new Date(this.day.date)
      if (this.day.combining_dates) {
        newDate.setMonth(newDate.getMonth() - 1)
      } else {
        newDate.setDate(newDate.getDate() - 1)
      }
      this.day.date = this.checkDate(newDate, false)
    },
    checkDate(date, plus=true) {
      let ownMonth = date.toISOMonth()
      let ownDate = date.toISODate()
      const direction = plus ? 1 : -1
      this.plannedDay = undefined

      // check if ownMonth or ownDate is in blockedTimes
      // while this is true add a day to the date
      while (this.blockedTimes.find(time => time === ownMonth || time === ownDate)) {
        if (this.day.combining_dates) {
          date.setMonth(date.getMonth() + direction)
        } else {
          date.setDate(date.getDate() + direction)
        }
        ownMonth = date.toISOMonth()
        ownDate = date.toISODate()
      }

      setTimeout(() => {
        this.loadPlan()
      }, 50)

      return date
    },
    loadPlan() {
      this.axios.get('days/?date=' + this.day.date.toISODate())
        .then(response => {
          if (response.data.length) {
            this.plannedDay = response.data[0]
          }
        })
    },
    toggleCombiningDates(day) {
      day.combining_dates = !day.combining_dates;
    },
    toggleDelivered() {
      // Wenn der Tag auf delivered gesetzt wird, sorgt der computed setter dafür, dass alle Meals ebenfalls delivered true sind
      this.allMealsDelivered = !this.day.delivered;
      this.axios.patch(`invoice-days/${this.day.id}/`, { delivered: this.day.delivered }).then(() => {
      });
    },
    toggleMealDelivered(meal) {
      meal.delivered = !meal.delivered;
    }
  },
  created () {
    if (!this.day.id) {
      let newDate = new Date(this.day.date)
      this.day.date = this.checkDate(newDate)

    }
  }
};
</script>

<style scoped lang="sass">
.dayDisplay
  margin-top: 1em
.meals
  margin: 12px -4px 12px -8px
  transition: all 0.5s

  &.withComment
    margin-bottom: 0
  border-left: 4px solid transparent

.withComment
  transition: all 0.5s
  border-left: 4px solid #ccc
  margin-left: -8px
  background-color: #f9f9f9
  &.comment
    margin-top: 0

.v-btn.delivery
  color: lightgray

.spacer-delivered
  width: 48px

.plannedMeal
  padding: 8px 0

.pointer
  cursor: pointer
</style>
