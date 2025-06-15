<template>
  <v-card>
    <v-card-title>
      <v-btn icon @click="$router.back()">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <span class="ml-2 font-weight-medium">Discussão do Exemplo #{{ exampleId }}</span>
      <v-spacer />
    </v-card-title>
    <v-card-text>
      <div v-if="loading" class="text-center pa-10">
        <v-progress-circular indeterminate color="primary" />
      </div>

      <div v-else>
        <!-- Texto original -->
        <v-card outlined class="mb-6 pa-4">
          <h3 class="subtitle-1 mb-2">Texto Original</h3>
          <p style="white-space: pre-wrap">{{ example?.text }}</p>
        </v-card>

        <!-- Comparação de Anotações -->
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
                  class="ma-1 clickable-chip"
                  color="primary"
                  text-color="white"
                  @click="handleChipClick(label)"
                >
                  {{ label }}
                </v-chip>
              </div>
            </v-col>
          </v-row>
        </v-card>

        <!-- Painel de Discussão -->
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
    </v-card-text>
  </v-card>
</template>

<script>
import { mapGetters } from 'vuex'
import ApiService from '@/services/api.service'

export default {
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],
  async asyncData({ params, error }) {
    const projectId = params.id
    const exampleId = params.exampleId
    try {
      const url = `/projects/${projectId}/examples/${exampleId}`
      const resp = await ApiService.get(url)
      return {
        projectId,
        exampleId,
        example: resp.data,
        loading: false,
        // UI / Annotations state
        labelOptions: [],
        selectedLabelId: null,
        annotations: [],
        groupedByLabel: {},
        comments: [],
        newComment: ''
      }
    } catch (e) {
      error({ statusCode: 404, message: 'Exemplo não encontrado' })
    }
  },
  computed: {
    ...mapGetters('auth', ['getUsername']),
    currentLabelText() {
      const opt = this.labelOptions.find((o) => o.id === this.selectedLabelId)
      return opt ? opt.text : ''
    }
  },
  mounted() {
    this.fetchAnnotations()
  },
  methods: {
    async fetchAnnotations() {
      try {
        const urlCat = `/projects/${this.projectId}/examples/${this.exampleId}/categories`
        const response = await ApiService.get(urlCat, { params: { all: 1 } })
        const categories = response.data
        // fetch label types to map id->text
        const labelTypes = await this.$services.categoryType.list(this.projectId)
        const labelMap = Object.fromEntries(labelTypes.map((l) => [l.id, l.text]))
        // fetch member list for username mapping
        const members = await this.$repositories.member.list(this.projectId)
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

        // Apenas labels anotadas pelo utilizador atual
        const selfUser = this.getUsername
        const userLabelEntries = Object.entries(groupedByLabel)
          .filter(([_, v]) => v.users[selfUser])

        this.labelOptions = userLabelEntries.map(([id, v]) => ({
          id: Number(id),
          text: v.text
        }))
        if (this.selectedLabelId === null && this.labelOptions.length) {
          this.selectedLabelId = this.labelOptions[0].id
        }
        this.groupedByLabel = groupedByLabel
        this.buildAnnotations(groupedByLabel)
        if (this.selectedLabelId) this.fetchComments()
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('Failed to fetch annotations', err)
        this.annotations = []
      }
    },
    async fetchComments() {
      try {
        if (this.selectedLabelId === null) { this.comments = []; return }
        this.comments = await this.$repositories.comment.list(
          this.projectId,
          Number(this.exampleId),
          this.selectedLabelId
        )
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
        const newComment = await this.$repositories.comment.create(
          this.projectId,
          Number(this.exampleId),
          this.newComment,
          this.selectedLabelId
        )
        this.comments.push(newComment)
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
      this.fetchComments()
    },
    handleChipClick(labelText) {
      const opt = this.labelOptions.find((o) => o.text === labelText)
      if (opt) {
        this.selectedLabelId = opt.id
        this.onLabelChange()
      }
    }
  }
}
</script>

<style scoped>
.subtitle-1 {
  font-weight: 500;
}

.clickable-chip {
  cursor: pointer;
}
</style> 