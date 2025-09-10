<template>
  <v-card>
    <v-toolbar color="primary white--text" flat>
      <v-toolbar-title>Assign examples to members</v-toolbar-title>
    </v-toolbar>
    <v-card-text>
      <v-container fluid>
        <v-row>
          <v-card-title class="pb-0 pl-3">Select assignment strategy</v-card-title>
          <v-col cols="12">
            <v-select
              v-model="selectedStrategy"
              :items="strategies"
              item-text="displayName"
              item-value="value"
              outlined
              dense
              hide-details
            ></v-select>
            {{ strategies.find((strategy) => strategy.value === selectedStrategy)?.description }}
            The project managers have access to all examples, regardless of whether they are
            assigned or not.
          </v-col>
        </v-row>
        <v-row>
          <v-card-title class="pb-0 pl-3">Allocate weights</v-card-title>
          <v-col v-for="(member, i) in members" :key="member.id" cols="12" class="pt-0 pb-0">
            <v-subheader class="pl-0">{{ member.username }}</v-subheader>
            <v-slider v-model="workloadAllocation[i]" :max="100" class="align-center">
              <template #append>
                <v-text-field
                  v-model="workloadAllocation[i]"
                  class="mt-0 pt-0"
                  type="number"
                  style="width: 60px"
                ></v-text-field>
              </template>
            </v-slider>
          </v-col>
        </v-row>
      </v-container>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn class="text-capitalize" text color="primary" data-test="cancel-button" @click="cancel">
        Cancel
      </v-btn>
      <v-btn
        class="text-none"
        text
        :disabled="!validateWeight || isWaiting"
        data-test="delete-button"
        @click="agree"
      >
        Assign
      </v-btn>
    </v-card-actions>

    <!-- Confirmation Dialog -->
    <v-dialog v-model="showConfirmDialog" max-width="500">
      <v-card>
        <v-card-title class="headline">Confirm Assignment</v-card-title>
        <v-card-text>
          Are you sure you want to assign members with the selected strategy and workloads?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary darken-1" text @click="showConfirmDialog = false">
            Cancel
          </v-btn>
          <v-btn color="primary darken-1" text @click="confirmAssignment">
            Confirm
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-overlay :value="isWaiting">
      <v-progress-circular indeterminate size="64" />
    </v-overlay>
  </v-card>
</template>

<script lang="ts">
import Vue from 'vue'
import { MemberItem } from '~/domain/models/member/member'

export default Vue.extend({
  data() {
    return {
      members: [] as MemberItem[],
      workloadAllocation: [] as number[],
      selectedStrategy: 'weighted_sequential',
      isWaiting: false,
      showConfirmDialog: false,
    }
  },

  async fetch() {
    this.members = await this.$repositories.member.list(this.projectId)
    this.workloadAllocation = this.members.map(() => Math.round(100 / this.members.length))
  },

  computed: {
    projectId() {
      return this.$route.params.id
    },

    strategies() {
      return [
        {
          displayName: 'Weighted sequential',
          value: 'weighted_sequential',
          description:
            'Assign examples to members in order of their workload. The total weight must equal 100.'
        },
        {
          displayName: 'Weighted random',
          value: 'weighted_random',
          description:
            'Assign examples to members randomly based on their workload. The total weight must equal 100.'
        },
        {
          displayName: 'Sampling without replacement',
          value: 'sampling_without_replacement',
          description: 'Assign examples to members randomly without replacement.'
        }
      ]
    },

    validateWeight(): boolean {
      if (this.selectedStrategy === 'sampling_without_replacement') {
        return true
      } else {
        return this.workloadAllocation.reduce((acc, cur) => acc + cur, 0) === 100
      }
    }
  },

  methods: {
    agree() {
      this.showConfirmDialog = true;
    },

    async confirmAssignment() {
      this.showConfirmDialog = false;
      console.log("Attempting to assign members.");
      this.isWaiting = true;
      const workloads = this.workloadAllocation.map((weight, i) => ({
        weight,
        member_id: this.members[i].id,
      }));
      console.log("Payload for bulkAssign:", { strategy_name: this.selectedStrategy, workloads });
      try {
        await this.$repositories.assignment.bulkAssign(this.projectId, {
          strategy_name: this.selectedStrategy,
          workloads,
        });
        console.log("Members assigned successfully.");
        this.$emit("assigned");
      } catch (error) {
        console.error("Error assigning members:", error);
        this.$toasted.error("Error assigning members. Please check console for details.");
      } finally {
        this.isWaiting = false;
      }
    },

    cancel() {
      console.log("Assignment cancelled.");
      this.$emit("cancel");
    },
  },
})
</script>

<style scoped>
/* Add your component-specific styles here */
</style>
