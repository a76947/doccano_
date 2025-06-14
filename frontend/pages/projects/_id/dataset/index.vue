<template>
  <v-card>
    <v-card-title v-if="isProjectAdmin">
      <action-menu
        @upload="$router.push('dataset/import')"
        @download="$router.push('dataset/export')"
        @assign="dialogAssignment = true"
        @reset="dialogReset = true"
        @compare="dialogCompareForm = true"
      />
      <v-btn
        class="text-capitalize ms-2"
        :disabled="!canDelete"
        outlined
        @click.stop="dialogDelete = true"
      >
        {{ $t('generic.delete') }}
      </v-btn>
      <v-spacer />
      <v-btn
        :disabled="!item.count"
        class="text-capitalize"
        color="error"
        @click="dialogDeleteAll = true"
      >
        {{ $t('generic.deleteAll') }}
      </v-btn>
      <v-dialog v-model="dialogDelete">
        <form-delete
          :selected="selected"
          :item-key="itemKey"
          @cancel="dialogDelete = false"
          @remove="remove"
        />
      </v-dialog>
      <v-dialog v-model="dialogDeleteAll">
        <form-delete-bulk @cancel="dialogDeleteAll = false" @remove="removeAll" />
      </v-dialog>
      <v-dialog v-model="dialogAssignment">
        <form-assignment @assigned="assigned" @cancel="dialogAssignment = false" />
      </v-dialog>
      <v-dialog v-model="dialogReset">
        <form-reset-assignment @cancel="dialogReset = false" @reset="resetAssignment" />
      </v-dialog>
      <v-dialog v-model="dialogCompareForm" max-width="500">
        <form-compare-annotations
          :project-id="projectId"
          :documents="item.items"
          :project-users="projectUsers"
          @cancel="dialogCompareForm = false"
          @compare="openComparisonDialog"
        />
      </v-dialog>
    </v-card-title>
    
    <image-list
      v-if="project.isImageProject"
      v-model="selected"
      :items="item.items"
      :is-admin="user.isProjectAdmin"
      :is-loading="isLoading"
      :members="members"
      :total="item.count"
      @update:query="updateQuery"
      @click:labeling="movePage"
      @assign="assign"
      @unassign="unassign"
    />
    <audio-list
      v-else-if="project.isAudioProject"
      v-model="selected"
      :items="item.items"
      :is-admin="user.isProjectAdmin"
      :is-loading="isLoading"
      :members="members"
      :total="item.count"
      @update:query="updateQuery"
      @click:labeling="movePage"
      @assign="assign"
      @unassign="unassign"
    />
    <document-list
      v-else
      v-model="selected"
      :items="item.items"
      :is-admin="user.isProjectAdmin"
      :is-loading="isLoading"
      :members="members"
      :total="item.count"
      @update:query="updateQuery"
      @click:labeling="movePage"
      @edit="editItem"
      @vote="openVotePage"
    />
<v-dialog v-model="dialogCompare" max-width="90%" height="80vh" content-class="comparison-dialog">
  <v-card class="comparison-card">
    <v-toolbar dark color="primary" dense>
      <v-btn icon @click="dialogCompare = false">
        <v-icon>mdi-close</v-icon>
      </v-btn>
      <v-toolbar-title>Annotation Comparison</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-chip small class="mr-2">
        <v-avatar left>
          <v-icon x-small>mdi-file-document</v-icon>
        </v-avatar>
        Document #{{ selectedDocumentId }}
      </v-chip>
    </v-toolbar>
    
    <!-- Comparison component -->
    <comparison-view
      v-if="dialogCompare"
      :project-id="projectId"
      :document-id="selectedDocumentId"
      :user1-id="comparisonUsers.user1"
      :user2-id="comparisonUsers.user2"
      :labels="project && project.labels ? project.labels : []"
      :users="projectUsers || []"
      @close="dialogCompare = false"
      @no-annotations="handleNoAnnotations"
    />
  </v-card>
</v-dialog>

<!-- Add this for showing no annotations message -->
<v-snackbar
  v-model="noAnnotationsSnackbar"
  :timeout="5000"
  color="warning"
>
  {{ noAnnotationsMessage }}
  <template v-slot:action="{ attrs }">
    <v-btn
      text
      v-bind="attrs"
      @click="noAnnotationsSnackbar = false"
    >
      Close
    </v-btn>
  </template>
</v-snackbar>
  </v-card>
</template>

<script lang="ts">
import _ from 'lodash'
import { mapGetters } from 'vuex'
import Vue from 'vue'
import { NuxtAppOptions } from '@nuxt/types'
import DocumentList from '@/components/example/DocumentList.vue'
import FormAssignment from '~/components/example/FormAssignment.vue'
import FormDelete from '@/components/example/FormDelete.vue'
import FormDeleteBulk from '@/components/example/FormDeleteBulk.vue'
import FormResetAssignment from '~/components/example/FormResetAssignment.vue'
import ActionMenu from '~/components/example/ActionMenu.vue'
import AudioList from '~/components/example/AudioList.vue'
import ImageList from '~/components/example/ImageList.vue'
import { getLinkToAnnotationPage } from '~/presenter/linkToAnnotationPage'
import { ExampleDTO, ExampleListDTO } from '~/services/application/example/exampleData'
import { MemberItem } from '~/domain/models/member/member'
import ComparisonView from '~/components/annotations/ComparisonView.vue'
import FormCompareAnnotations from '~/components/example/FormCompareAnnotations.vue'

export default Vue.extend({
  components: {
    ActionMenu,
    AudioList,
    DocumentList,
    ImageList,
    FormAssignment,
    FormDelete,
    FormDeleteBulk,
    FormResetAssignment,
    FormCompareAnnotations, // Add this line
    ComparisonView
  },

  layout: 'project',

  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  validate({ params, query }: NuxtAppOptions) {
    return /^\d+$/.test(params.id) && /^\d+|$/.test(query.limit) && /^\d+|$/.test(query.offset)
  },

  data() {
    return {
      dialogDelete: false,
      dialogDeleteAll: false,
      dialogAssignment: false,
      dialogReset: false,
      dialogCompare: false,
      dialogCompareForm: false,
      item: {} as ExampleListDTO,
      selected: [] as ExampleDTO[],
      members: [] as MemberItem[],
      user: {} as MemberItem,
      isLoading: false,
      isProjectAdmin: false,
      selectedDocumentId: null,
      comparisonUsers: {
        user1: null,
        user2: null
      },
      projectUsers: [],
      noAnnotationsSnackbar: false,
      noAnnotationsMessage: '',
    }
  },

  async fetch() {
    this.isLoading = true
    this.item = await this.$services.example.list(this.projectId, this.$route.query)
    this.user = await this.$repositories.member.fetchMyRole(this.projectId)
    
    // Only load members if user is admin
    if (this.user.isProjectAdmin) {
      try {
        this.members = await this.$repositories.member.list(this.projectId)
      } catch (error) {
        console.warn('Could not load project members:', error)
        this.members = []
      }
    } else {
      // For regular users, only include themselves
      this.members = [this.user]
    }
    
    this.isLoading = false
  },

  computed: {
    ...mapGetters('projects', ['project']),

    canDelete(): boolean {
      return this.selected.length > 0
    },

    projectId(): string {
      return this.$route.params.id
    },

    itemKey(): string {
      if (this.project.isImageProject || this.project.isAudioProject) {
        return 'filename'
      } else {
        return 'text'
      }
    }
  },

  watch: {
    '$route.query': _.debounce(function () {
      // @ts-ignore
      this.$fetch()
    }, 1000)
  },

  async created() {
    const member = await this.$repositories.member.fetchMyRole(this.projectId)
    this.isProjectAdmin = member.isProjectAdmin
    
    // Only load project members if user is an admin
    if (this.isProjectAdmin) {
      try {
        this.projectUsers = await this.$repositories.member.list(this.projectId)
      } catch (error) {
        console.warn('Could not load project members:', error)
        this.projectUsers = []
      }
    } else {
      // For regular users, only include themselves
      this.projectUsers = [member]
    }
  },

  methods: {
    async remove() {
      await this.$services.example.bulkDelete(this.projectId, this.selected)
      this.$fetch()
      this.dialogDelete = false
      this.selected = []
    },

    async removeAll() {
      await this.$services.example.bulkDelete(this.projectId, [])
      this.$fetch()
      this.dialogDeleteAll = false
      this.selected = []
    },

    updateQuery(query: object) {
      this.$router.push(query)
    },

    movePage(query: object) {
      const link = getLinkToAnnotationPage(this.projectId, this.project.projectType)
      this.updateQuery({
        path: this.localePath(link),
        query
      })
    },

    editItem(item: ExampleDTO) {
      this.$router.push(`dataset/${item.id}/edit`)
    },

    async assign(exampleId: number, userId: number) {
      await this.$repositories.assignment.assign(this.projectId, exampleId, userId)
      this.item = await this.$services.example.list(this.projectId, this.$route.query)
    },

    async unassign(assignmentId: string) {
      await this.$repositories.assignment.unassign(this.projectId, assignmentId)
      this.item = await this.$services.example.list(this.projectId, this.$route.query)
    },

    async assigned() {
      this.dialogAssignment = false
      this.item = await this.$services.example.list(this.projectId, this.$route.query)
    },

    async resetAssignment() {
      this.dialogReset = false
      await this.$repositories.assignment.reset(this.projectId)
      this.item = await this.$services.example.list(this.projectId, this.$route.query)
    },

    async openComparisonDialog({ documentId, user1, user2 }) {
      console.log('Opening comparison dialog with:', { documentId, user1, user2 });
      
      try {
        // Get document text first to make sure document exists
        await this.$services.example.findById(this.projectId, documentId);
        
        // Check if annotations exist
        let annotationData;
        try {
          annotationData = await this.$repositories.annotation.getComparisonData(
            this.projectId,
            documentId,
            user1,
            user2
          );
        } catch (error) {
          console.error('Error fetching annotations:', error);
          this.handleNoAnnotations({
            message: `Error loading annotations: ${error.message}`
          });
          return;
        }
        
        // Verify annotations exist for both users
        if (!annotationData.user1.length && !annotationData.user2.length) {
          this.handleNoAnnotations({
            message: 'No annotations found for either user on this document.'
          });
          return;
        } else if (!annotationData.user1.length) {
          this.handleNoAnnotations({
            message: `No annotations found for First User on this document.`
          });
          return;
        } else if (!annotationData.user2.length) {
          this.handleNoAnnotations({
            message: `No annotations found for Second User on this document.`
          });
          return;
        }
        
        // If we get here, both users have annotations, so show the dialog
        this.selectedDocumentId = documentId;
        this.comparisonUsers = { user1, user2 };
        
        // Only try to get members if admin
        if (this.isProjectAdmin && (!this.projectUsers || this.projectUsers.length === 0)) {
          try {
            this.projectUsers = await this.$repositories.member.list(this.projectId);
            console.log('Loaded project users:', this.projectUsers.length);
          } catch (error) {
            console.warn('Could not load project users:', error);
            // Continue without user details
            this.projectUsers = [];
          }
        }
        
        this.dialogCompare = true;
        
      } catch (error) {
        console.error('Error checking document:', error);
        this.handleNoAnnotations({
          message: `Couldnt connect to the database, try again later.`
        });
      }
    },

    // Helper method to get user name
    getUserName(userId) {
      // Find user in projectUsers
      if (this.projectUsers && Array.isArray(this.projectUsers)) {
        const user = this.projectUsers.find(u => u.id === parseInt(userId) || u.id === userId);
        if (user && user.username) {
          return user.username;
        }
      }
      return `User ${userId}`;
    },

    handleNoAnnotations({ message }) {
      this.noAnnotationsMessage = message;
      this.noAnnotationsSnackbar = true;
      this.dialogCompare = false; // Close the comparison dialog
    },

    openVotePage(item) {
      // Make sure item exists and has necessary data
      if (!item || !item.id) {
        console.warn('No document selected for voting');
        return;
      }
      
      // Navigate to votacoes page with document info
      this.$router.push({
        path: `/projects/${this.projectId}/votacoes`,
        query: { 
          documentId: item.id,
          documentTitle: item.text || `Document #${item.id}`
        }
      });
    }
  }
})
</script>

<style scoped>
/* Style for the comparison dialog */
::v-deep .comparison-dialog {
  margin: 24px;
  height: calc(100vh - 48px) !important;
  max-height: calc(100vh - 48px) !important;
  display: flex;
  justify-content: center;
}

::v-deep .comparison-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

/* Add a subtle shadow to make it feel like a floating card */
::v-deep .v-card.comparison-card {
  box-shadow: 0 8px 36px rgba(0, 0, 0, 0.2) !important;
}

/* Keep your existing styles for non-fullscreen dialogs */
::v-deep .v-dialog:not(.v-dialog--fullscreen) {
  width: 800px;
}
</style>
