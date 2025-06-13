<template>
  <v-card elevation="0" class="discrepancy-page">
    <!-- Page header -->
    <v-card-title class="align-center">
      <h2 class="text-h5 mb-0">Discrepâncias</h2>
      <v-spacer />
      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Pesquisar"
        dense
        hide-details
        solo
        flat
        class="ma-0"
      />
      <v-select
        v-model="statusFilter"
        :items="statusItems"
        label="Status"
        dense
        hide-details
        solo
        flat
        class="ms-2"
      />
    </v-card-title>
    <v-divider />

    <!-- Content -->
    <v-row no-gutters>
      <!-- List of discrepancies -->
      <v-col cols="3" class="pa-2 list-col">
        <v-list dense shaped>
          <v-subheader class="text-body-2">Exemplos com discrepâncias</v-subheader>
          <v-list-item
            v-for="item in filteredExamples"
            :key="item.id"
            :value="item"
            :class="selected && selected.id === item.id ? 'grey lighten-4' : ''"
            @click="selectExample(item)"
          >
            <v-list-item-content>
              <v-list-item-title class="text-truncate" v-text="item.text" />
              <v-list-item-subtitle class="text-caption">
                Diferenças: {{ item.diffCount }}
              </v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-col>

      <!-- Viewer + discussion -->
      <v-col cols="9" class="pa-4 viewer-col">
        <div v-if="!selected" class="text-center grey--text mt-10">
          Selecione um exemplo para visualizar as anotações.
        </div>
        <div v-else>
          <!-- Original text -->
          <v-card outlined class="mb-6 pa-4">
            <h3 class="subtitle-1 mb-2">Texto Original</h3>
            <p class="mb-0" style="white-space: pre-wrap">{{ selected.text }}</p>
          </v-card>

          <!-- Diff visualization -->
          <v-card outlined class="mb-6 pa-4">
            <div class="d-flex align-center mb-4">
              <h3 class="subtitle-1 mr-4 mb-0">Comparação de Anotações</h3>
              <v-select
                v-if="labelOptions.length"
                v-model="selectedLabelId"
                :items="labelOptions"
                item-text="text"
                item-value="id"
                dense
                hide-details
                outlined
                style="max-width: 200px"
                label="Label"
                @change="onLabelChange"
              />
            </div>
            <div v-if="annotations.length === 0" class="text-center grey--text caption">
              Sem anotações para comparar.
            </div>
            <v-row v-else>
              <v-col
                v-for="ann in annotations"
                :key="ann.user"
                cols="6"
                class="pb-4"
              >
                <strong>{{ ann.user }}</strong>
                <div class="mt-2">
                  <v-chip
                    v-for="label in ann.labels"
                    :key="label"
                    small
                    class="ma-1"
                    color="primary"
                    text-color="white"
                  >
                    {{ label }}
                  </v-chip>
                </div>
              </v-col>
            </v-row>
          </v-card>

          <!-- Discussion panel -->
          <v-card outlined>
            <h3 class="subtitle-1 pa-4 pb-0">Discussão - Label {{ currentLabelText }}</h3>
            <v-list dense two-line class="py-0">
              <v-list-item v-for="c in comments" :key="c.id">
                <v-list-item-content>
                  <v-list-item-title>{{ c.username }}</v-list-item-title>
                  <v-list-item-subtitle>{{ c.text }}</v-list-item-subtitle>
                </v-list-item-content>
                <v-list-item-action-text class="grey--text text-caption">
                  {{ formatTime(c.createdAt) }}
                </v-list-item-action-text>
              </v-list-item>
            </v-list>
            <v-divider />
            <v-card-actions>
              <v-text-field
                v-model="newComment"
                label="Adicionar comentário..."
                dense
                hide-details
                outlined
                class="flex-grow-1"
                @keyup.enter="sendComment"
              />
              <v-btn icon :disabled="!newComment" @click="sendComment">
                <v-icon>mdi-send</v-icon>
              </v-btn>
            </v-card-actions>
          </v-card>
        </div>
      </v-col>
    </v-row>
  </v-card>
</template>

<script>
import { mapGetters } from 'vuex'
import ApiService from '@/services/api.service'

export default {
  name: 'DiscrepanciesPage',
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],
  validate({ params }) {
    return /^\d+$/.test(params.id)
  },
  data() {
    return {
      // UI state
      search: '',
      statusFilter: 'all',
      statusItems: [
        { text: 'Todos', value: 'all' },
        { text: 'Por Resolver', value: 'open' },
        { text: 'Resolvidos', value: 'resolved' }
      ],
      // Data from API
      examples: [],
      selected: null,
      // Discussion
      comments: [],
      newComment: '',
      annotations: [],
      labelOptions: [],
      selectedLabelId: null,
      groupedByLabel: {},
    }
  },
  computed: {
    ...mapGetters('auth', ['getUsername']),
    filteredExamples() {
      let list = this.examples
      if (this.statusFilter !== 'all') {
        list = list.filter((e) => e.status === this.statusFilter)
      }
      if (this.search) {
        const q = this.search.toLowerCase()
        list = list.filter((e) => e.text.toLowerCase().includes(q))
      }
      return list
    },
    currentLabelText() {
      const opt = this.labelOptions.find((o) => o.id === this.selectedLabelId)
      return opt ? opt.text : ''
    }
  },
  async created() {
    await this.fetchExamples()
  },
  methods: {
    async fetchExamples() {
      try {
        const projectId = this.$route.params.id
        const list = await this.$repositories.discrepancy.list(projectId)
        this.examples = list.map((e) => ({
          id: e.id,
          text: e.text,
          diffCount: e.diff_count || e.diffCount || e.max_percentage || 0,
          status: e.is_discrepancy ? 'open' : 'resolved',
          maxPercentage: e.max_percentage || 0,
          percentages: e.percentages || {}
        }))
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error('Failed to load discrepancies', e)
      }
    },
    async fetchAnnotationsForExample(example) {
      try {
        const projectId = this.$route.params.id
        const urlCat = `/projects/${projectId}/examples/${example.id}/categories`
        const response = await ApiService.get(urlCat, { params: { all: 1 } })
        const categories = response.data
        // fetch label types to map id->text
        const labelTypes = await this.$services.categoryType.list(projectId)
        const labelMap = Object.fromEntries(labelTypes.map((l) => [l.id, l.text]))
        // fetch member list for username mapping
        const members = await this.$repositories.member.list(projectId)
        const userMap = Object.fromEntries(members.map((m) => [m.id, m.username]))
        // collect label info and group users by label
        const groupedByLabel = {}
        categories.forEach((c) => {
          const user = userMap[c.user] || c.user
          const labelId = c.label
          const labelText = labelMap[labelId] || labelId
          if (!groupedByLabel[labelId]) groupedByLabel[labelId] = { text: labelText, users: {} }
          if (!groupedByLabel[labelId].users[user]) groupedByLabel[labelId].users[user] = new Set()
          groupedByLabel[labelId].users[user].add(labelText)
        })
        // create annotations list for selected label only later
        this.labelOptions = Object.entries(groupedByLabel).map(([id, v]) => ({
          id: Number(id),
          text: v.text
        }))
        if (this.selectedLabelId === null && this.labelOptions.length) {
          this.selectedLabelId = this.labelOptions[0].id
        }
        this.groupedByLabel = groupedByLabel
        this.buildAnnotations(groupedByLabel)
        if (this.selectedLabelId) this.fetchComments(this.selected)
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('Failed to fetch annotations', err)
        this.annotations = []
      }
    },
    selectExample(item) {
      this.selected = item
      this.fetchAnnotationsForExample(item)
      this.fetchComments(item)
    },
    async fetchComments(example) {
      try {
        const projectId = this.$route.params.id
        if (this.selectedLabelId === null) { this.comments = []; return }
        const res = await this.$repositories.comment.list(
          projectId,
          example.id,
          this.selectedLabelId
        )
        this.comments = res.filter((c) => Number(c.label) === this.selectedLabelId)
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('Failed to load comments', err)
        this.comments = []
      }
    },
    formatTime(iso) {
      return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    },
    async sendComment() {
      if (!this.newComment) return
      try {
        const projectId = this.$route.params.id
        const exampleId = this.selected.id
        const newC = await this.$repositories.comment.create(
          projectId,
          exampleId,
          this.newComment,
          this.selectedLabelId
        )
        if (Number(newC.label) === this.selectedLabelId) this.comments.push(newC)
        this.newComment = ''
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('Failed to send comment', err)
      }
    },
    buildAnnotations(grouped) {
      if (!this.selectedLabelId) { this.annotations = []; return }
      const entry = grouped[this.selectedLabelId]
      if (!entry) { this.annotations = []; return }
      this.annotations = Object.entries(entry.users).map(([user, labels]) => ({
        user,
        labels: Array.from(labels)
      }))
    },
    onLabelChange() {
      this.comments = []
      this.buildAnnotations(this.groupedByLabel)
      if (this.selected) this.fetchComments(this.selected)
    },
  }
}
</script>

<style scoped>
.discrepancy-page {
  height: calc(100vh - 120px); /* ajusta consoante o header do layout */
  display: flex;
  flex-direction: column;
}
.list-col {
  border-right: 1px solid #eeeeee;
  overflow-y: auto;
  height: calc(100vh - 160px);
}
.viewer-col {
  overflow-y: auto;
  height: calc(100vh - 160px);
}
</style> 