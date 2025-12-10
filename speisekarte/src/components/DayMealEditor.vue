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
        v-btn-toggle(dense borderless)
          v-btn(
            v-if="!day.id"
            :color="day.combining_dates ? 'primary' : 'default'"
            @click="toggleCombiningDates(day)"
          )
            v-icon mdi-calendar-month-outline
          v-btn.delivery(
            v-if="day.id && day.date < new Date()"
            :class="{delivered: day.delivered}"
            @click="toggleDelivered" :color="day.delivered ? 'success' : 'error'") ✓

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
            suffix="€"
            @blur="updateMeal(meal)"
            hide-details
          )
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
          @blur="updateMeal"
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
    }
  },
  computed: {
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
    updateMeal(meal) {
      // Prüfe, ob alle erforderlichen Felder im newMeal gesetzt sind
      if (meal.name && meal.price) {
        // Falls der Tag noch keine id besitzt, muss er zuerst angelegt werden
        if (!this.day.id) {
          // Falls day.customer noch nicht gesetzt ist, übernehmen wir den Kunden
          if (!this.day.customer && this.customer && this.customer.id) {
            this.day.customer = this.customer.id;
          }
          // Formatieren des Datums (nur Datum, ohne Uhrzeit)
          const formattedDate = new Date(this.day.date).toISOString().split('T')[0];
          this.day.date = formattedDate;
          this.axios.post('invoice-days/', this.day)
            .then(response => {
              // Setze die zurückgegebene ID in den day
              this.day.id = response.data.id
              this.updateMeal(meal)
            })
        } else {

          if (!meal.day) {
            meal.day = this.day.id
          }

          if (meal.id) {

            // Meal löschen, wenn count 0 ist
            if(meal.count == 0) {
              this.axios.delete(`invoice-meals/${meal.id}/`)
                .then(() => {
                  if (this.day.meals.length === 1) {
                    this.deleteDay()
                  } else { this.loadMeals() }
                })
            } else {
              this.axios.patch(`invoice-meals/${meal.id}/`, meal)
                .then(() => {
                })
            }

          } else {

            this.axios.post('invoice-meals/', meal)
              .then(() => {
                this.newMeal = { name: '', count: 1, price: '', delivered: false }
                this.loadMeals()
                this.$emit('new-day-created')
              })
          }
        }
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
