<template>
  <div class="comparison-container">
    <!-- Elegant header with user info -->
    <div class="d-flex align-center justify-space-between px-4 py-3 header">
      <div class="d-flex align-center">
        <v-icon color="primary" class="mr-2">mdi-compare</v-icon>
        <h3 class="text-h6 font-weight-medium mb-0">Annotation Comparison</h3>
      </div>
      <div class="d-flex align-center user-badges">
        <v-chip small color="#fff3e0" text-color="#e65100" class="mr-2">
          <v-avatar left size="24" class="mr-1">
            <v-icon x-small>mdi-account</v-icon>
          </v-avatar>
          {{ getUserName(user1Id) }}
        </v-chip>
        <v-icon small>mdi-compare-horizontal</v-icon>
        <v-chip small color="#e3f2fd" text-color="#0d47a1" class="ml-2">
          <v-avatar left size="24" class="mr-1">
            <v-icon x-small>mdi-account</v-icon>
          </v-avatar>
          {{ getUserName(user2Id) }}
        </v-chip>
      </div>
    </div>
    
    <!-- Label legend as chips -->
    <div class="px-4 py-2 grey lighten-5 d-flex align-center label-legend">
      <div class="mr-3 grey--text text--darken-1">
        <v-icon x-small class="mr-1">mdi-palette</v-icon>
        <span class="text-caption font-weight-medium">Labels:</span>
      </div>
      <v-chip
        v-for="label in effectiveLabels"
        :key="label.id"
        x-small
        :style="{
          backgroundColor: label.backgroundColor,
          color: getContrastColor(label.backgroundColor)
        }"
        class="mr-2"
      >
        {{ label.text }}
      </v-chip>
    </div>

    <!-- Side-by-side document views -->
    <div class="side-by-side-container">
      <!-- User 1 view -->
      <div class="document-panel">
        <div class="document-header px-4 py-2">
          <v-chip small color="#fff3e0" text-color="#e65100">
            <v-avatar left size="24" class="mr-1">
              <v-icon x-small>mdi-account</v-icon>
            </v-avatar>
            {{ getUserName(user1Id) }}
          </v-chip>
          <div class="text-caption grey--text ml-2">
            {{ user1Annotations.length }} annotations
          </div>
        </div>
        <div class="document-content" ref="user1Content" @scroll="syncScroll(1, $event)">
          <div class="document-text">
            <template v-if="documentText">
              <span
                v-for="(segment, i) in user1Segments"
                :key="i"
                :class="segment.classes"
                :style="segment.style"
                :title="segment.title"
              >
                {{ segment.text }}
              </span>
            </template>
            <div v-else class="text-center py-4 grey--text">
              No document text available
            </div>
          </div>
        </div>
      </div>

      <!-- User 2 view -->
      <div class="document-panel">
        <div class="document-header px-4 py-2">
          <v-chip small color="#e3f2fd" text-color="#0d47a1">
            <v-avatar left size="24" class="mr-1">
              <v-icon x-small>mdi-account</v-icon>
            </v-avatar>
            {{ getUserName(user2Id) }}
          </v-chip>
          <div class="text-caption grey--text ml-2">
            {{ user2Annotations.length }} annotations
          </div>
        </div>
        <div class="document-content" ref="user2Content" @scroll="syncScroll(2, $event)">
          <div class="document-text">
            <template v-if="documentText">
              <span
                v-for="(segment, i) in user2Segments"
                :key="i"
                :class="segment.classes"
                :style="segment.style"
                :title="segment.title"
              >
                {{ segment.text }}
              </span>
            </template>
            <div v-else class="text-center py-4 grey--text">
              No document text available
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Enhanced agreement statistics bar at bottom -->
    <div class="agreement-stats-bar">
      <div class="stats-container pa-4">
        <div class="stats-card pa-3">
          <div class="d-flex align-center mb-3">
            <v-icon color="primary" class="mr-2">mdi-chart-bar</v-icon>
            <span class="text-subtitle-2 font-weight-medium">Agreement Statistics</span>
          </div>
          
          <div class="d-flex flex-wrap justify-space-between">
            <div class="stat-box match-box">
              <div class="stat-value">{{ matchingCount }}</div>
              <div class="stat-label">
                <v-icon small color="green" class="mr-1">mdi-check-circle</v-icon>
                Matching
              </div>
            </div>
            
            <div class="stat-box user1-box">
              <div class="stat-value">{{ user1OnlyCount }}</div>
              <div class="stat-label">
                <v-avatar size="16" class="user1-badge mr-1"></v-avatar>
                {{ getUserName(user1Id) }} only
              </div>
            </div>
            
            <div class="stat-box user2-box">
              <div class="stat-value">{{ user2OnlyCount }}</div>
              <div class="stat-label">
                <v-avatar size="16" class="user2-badge mr-1"></v-avatar>
                {{ getUserName(user2Id) }} only
              </div>
            </div>
            
            <div class="stat-box agreement-box">
              <div class="agreement-ring">
                <v-progress-circular
                  :size="54"
                  :width="6"
                  :value="agreementPercentage"
                  :color="getAgreementColor(agreementPercentage)"
                >
                  <span class="text-h6">{{ agreementPercentage }}%</span>
                </v-progress-circular>
              </div>
              <div class="stat-label text-center mt-2">
                <v-chip
                  x-small
                  :color="getAgreementColor(agreementPercentage)"
                  text-color="white"
                >
                  Agreement
                </v-chip>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Vue from 'vue'

export default Vue.extend({
  props: {
    projectId: {
      type: [Number, String],
      required: true
    },
    documentId: {
      type: [Number, String],
      required: true
    },
    user1Id: {
      type: [Number, String],
      required: true
    },
    user2Id: {
      type: [Number, String],
      required: true
    },
    labels: {
      type: Array,
      default: () => []
    },
    users: {
      type: Array,
      default: () => []
    }
  },

  data() {
    return {
      loading: true,
      documentText: '',
      user1Annotations: [],
      user2Annotations: [],
      matchingCount: 0,
      user1OnlyCount: 0,
      user2OnlyCount: 0,
      debug: true,
      errorMessage: null,
      projectLabels: [], // Add this to store fetched project labels
      apiLoaded: false, // Add this flag
      // Add default labels for testing
      defaultLabels: [
        { id: 1, text: "Good", backgroundColor: "#4CAF50" },
        { id: 2, text: "Bad", backgroundColor: "#F44336" },
        { id: 3, text: "MEh", backgroundColor: "#FFC107" }
      ],
      isScrollingSynced: false,
    }
  },

  computed: {
    // Use project labels, then props, then defaults
    effectiveLabels() {
      if (this.projectLabels && this.projectLabels.length > 0) {
        return this.projectLabels;
      } else if (this.labels && this.labels.length > 0) {
        return this.labels;
      }
      return this.defaultLabels;
    },
    
    agreementPercentage() {
      const total = this.matchingCount + this.user1OnlyCount + this.user2OnlyCount
      if (total === 0) return 0
      return Math.round((this.matchingCount / total) * 100)
    },

    // Add this new computed property for highlighted document
    highlightedDocument() {
      if (!this.documentText) return [];
      
      // Get all annotations combined
      const allAnnotations = [];
      
      // Add User 1 annotations
      this.user1Annotations.forEach(ann => {
        allAnnotations.push({
          start: ann.start_offset,
          end: ann.end_offset,
          label: ann.label,
          user: 1
        });
      });
      
      // Add User 2 annotations
      this.user2Annotations.forEach(ann => {
        allAnnotations.push({
          start: ann.start_offset,
          end: ann.end_offset,
          label: ann.label,
          user: 2
        });
      });
      
      // Sort by start position
      allAnnotations.sort((a, b) => a.start - b.start);
      
      // Build segments
      const segments = [];
      let lastEnd = 0;
      
      for (let i = 0; i < allAnnotations.length; i++) {
        const ann = allAnnotations[i];
        
        // Add non-highlighted text before this annotation
        if (ann.start > lastEnd) {
          segments.push({
            text: this.documentText.substring(lastEnd, ann.start),
            classes: '',
            style: {},
            title: ''
          });
        }
        
        // Check for match or unique annotation
        const isMatch = this.isMatchingAnnotation(ann);
        
        // Add the highlighted text
        segments.push({
          text: this.documentText.substring(ann.start, ann.end),
          classes: isMatch ? 'highlight-match' : (ann.user === 1 ? 'highlight-user1' : 'highlight-user2'),
          style: {
            backgroundColor: isMatch ? '#c8e6c9' : (ann.user === 1 ? '#ffecb3' : '#bbdefb'),
            borderBottom: `2px solid ${this.getColorForLabel(ann.label)}`,
            padding: '0 2px',
          },
          title: `${this.getLabelText(ann.label)} - ${isMatch ? 'Both users' : (ann.user === 1 ? this.getUserName(this.user1Id) : this.getUserName(this.user2Id))}`
        });
        
        lastEnd = Math.max(lastEnd, ann.end);
      }
      
      // Add remaining text
      if (lastEnd < this.documentText.length) {
        segments.push({
          text: this.documentText.substring(lastEnd),
          classes: '',
          style: {},
          title: ''
        });
      }
      
      return segments;
    },

    

    baseSegments() {
      if (!this.documentText) return [];
      
      // Create common segments based on all annotations
      const allAnnotations = [
        ...this.user1Annotations.map(a => ({ 
          position: a.start_offset, 
          isStart: true, 
          user: 1,
          annotation: a 
        })),
        ...this.user1Annotations.map(a => ({ 
          position: a.end_offset, 
          isStart: false, 
          user: 1,
          annotation: a 
        })),
        ...this.user2Annotations.map(a => ({ 
          position: a.start_offset, 
          isStart: true, 
          user: 2,
          annotation: a 
        })),
        ...this.user2Annotations.map(a => ({ 
          position: a.end_offset, 
          isStart: false, 
          user: 2,
          annotation: a 
        }))
      ];
      
      // Sort by position
      allAnnotations.sort((a, b) => {
        if (a.position !== b.position) return a.position - b.position;
        // If positions are the same, ends come before starts
        return a.isStart ? 1 : -1;
      });
      
      // Create segments
      const segments = [];
      let lastPos = 0;
      
      for (const point of allAnnotations) {
        if (point.position > lastPos) {
          segments.push({
            start: lastPos,
            end: point.position,
            text: this.documentText.substring(lastPos, point.position),
            annotations: [] // No annotations for this segment
          });
        }
        lastPos = point.position;
      }
      
      // Add remaining text if any
      if (lastPos < this.documentText.length) {
        segments.push({
          start: lastPos,
          end: this.documentText.length,
          text: this.documentText.substring(lastPos),
          annotations: []
        });
      }
      
      return segments;
    },
    
    // User 1 segments - now using the common base segments
    user1Segments() {
      return this.baseSegments.map(segment => {
        // Find annotations that cover this segment for user 1
        const activeAnnotations = this.user1Annotations.filter(ann => 
          ann.start_offset <= segment.start && ann.end_offset >= segment.end
        );
        
        if (activeAnnotations.length > 0) {
          // Find if any of these annotations match with user 2
          const matchingAnn = activeAnnotations.find(ann => 
            this.user2Annotations.some(a => 
              a.start_offset === ann.start_offset && 
              a.end_offset === ann.end_offset && 
              a.label === ann.label
            )
          );
          
          if (matchingAnn) {
            return {
              text: segment.text,
              classes: 'highlight-match',
              style: {
                backgroundColor: '#c8e6c9',
                borderBottom: `2px solid ${this.getColorForLabel(matchingAnn.label)}`,
                padding: '0 2px',
              },
              title: `${this.getLabelText(matchingAnn.label)} - Matches with ${this.getSafeUserName(this.user2Id)}`
            };
          } else {
            // User 1 only annotation
            return {
              text: segment.text,
              classes: 'highlight-user1',
              style: {
                backgroundColor: '#ffecb3',
                borderBottom: `2px solid ${this.getColorForLabel(activeAnnotations[0].label)}`,
                padding: '0 2px',
              },
              title: `${this.getLabelText(activeAnnotations[0].label)} - Only by ${this.getSafeUserName(this.user1Id)}`
            };
          }
        } else {
          // No annotation for this segment
          return {
            text: segment.text,
            classes: '',
            style: {},
            title: ''
          };
        }
      });
    },
    
    // User 2 segments - now using the common base segments
    user2Segments() {
      return this.baseSegments.map(segment => {
        // Find annotations that cover this segment for user 2
        const activeAnnotations = this.user2Annotations.filter(ann => 
          ann.start_offset <= segment.start && ann.end_offset >= segment.end
        );
        
        if (activeAnnotations.length > 0) {
          // Find if any of these annotations match with user 1
          const matchingAnn = activeAnnotations.find(ann => 
            this.user1Annotations.some(a => 
              a.start_offset === ann.start_offset && 
              a.end_offset === ann.end_offset && 
              a.label === ann.label
            )
          );
          
          if (matchingAnn) {
            return {
              text: segment.text,
              classes: 'highlight-match',
              style: {
                backgroundColor: '#c8e6c9',
                borderBottom: `2px solid ${this.getColorForLabel(matchingAnn.label)}`,
                padding: '0 2px',
              },
              title: `${this.getLabelText(matchingAnn.label)} - Matches with ${this.getSafeUserName(this.user1Id)}`
            };
          } else {
            // User 2 only annotation
            return {
              text: segment.text,
              classes: 'highlight-user2',
              style: {
                backgroundColor: '#bbdefb',
                borderBottom: `2px solid ${this.getColorForLabel(activeAnnotations[0].label)}`,
                padding: '0 2px',
              },
              title: `${this.getLabelText(activeAnnotations[0].label)} - Only by ${this.getSafeUserName(this.user2Id)}`
            };
          }
        } else {
          // No annotation for this segment
          return {
            text: segment.text,
            classes: '',
            style: {},
            title: ''
          };
        }
      });
    },
  },

  mounted() {
    console.log("ComparisonView mounted with props:", {
      projectId: this.projectId,
      documentId: this.documentId,
      user1Id: this.user1Id,
      user2Id: this.user2Id,
      labels: this.labels?.length || 0,
      users: this.users?.length || 0
    });
    
    // Fetch project labels if not provided
    this.fetchProjectLabels();
    
    // Also try API data
    this.fetchData();
  },

  methods: {
    useTestData() {
      console.log("Loading test data");
      // Sample document text
      this.documentText = "This is a sample document text for demonstration purposes. It will help visualize annotations from different users."
      
      // Sample annotations
      this.user1Annotations = [
        { id: 101, start_offset: 5, end_offset: 11, label: 1 },
        { id: 102, start_offset: 27, end_offset: 38, label: 2 }
      ]
      
      this.user2Annotations = [
        { id: 201, start_offset: 5, end_offset: 11, label: 1 },
        { id: 202, start_offset: 44, end_offset: 54, label: 3 }
      ]
      
      // Calculate metrics
      this.calculateAgreementMetrics()
    },
    
    getUserName(userId) {
      return this.getSafeUserName(userId);
    },

    getLabelText(labelId) {
      const label = this.effectiveLabels.find(l => l.id === labelId || l.id === parseInt(labelId));
      return label ? label.text : `Label ${labelId}`;
    },

    getColorForLabel(labelId) {
      // Return gray for null
      if (labelId === null || labelId === undefined) return '#e0e0e0';
      
      // Find in effective labels (falls back to default labels)
      const label = this.effectiveLabels.find(l => l.id === labelId || l.id === parseInt(labelId));
      return label ? label.backgroundColor : '#cccccc';
    },

    getContrastColor(hexColor) {
      // If no color or invalid format, return black
      if (!hexColor || !hexColor.startsWith('#')) return '#000000';
      
      // Convert hex to RGB
      const r = parseInt(hexColor.slice(1, 3), 16);
      const g = parseInt(hexColor.slice(3, 5), 16);
      const b = parseInt(hexColor.slice(5, 7), 16);
      
      // Calculate luminance
      const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
      
      // Return black for light colors, white for dark colors
      return luminance > 0.5 ? '#000000' : '#FFFFFF';
    },

    getAgreementColor(percentage) {
      if (percentage >= 80) return 'success';
      if (percentage >= 60) return 'primary';
      if (percentage >= 40) return 'warning';
      return 'error';
    },

    async fetchData() {
      this.loading = true
      try {
        // Fetch document text
        const doc = await this.$services.example.findById(this.projectId, this.documentId)
        this.documentText = doc.text
        
        try {
          // Try to get annotations using the repository
          const annotationData = await this.$repositories.annotation.getComparisonData(
            this.projectId,
            this.documentId,
            this.user1Id,
            this.user2Id
          );
          
          // Check if we have annotations from both users
          if (!annotationData.user1.length && !annotationData.user2.length) {
            // Both users have no annotations, emit an event to notify parent
            this.$emit('no-annotations', {
              message: 'No annotations found for either user on this document.'
            });
            return; // Exit the method early
          } else if (!annotationData.user1.length) {
            // User 1 has no annotations
            this.$emit('no-annotations', {
              message: `No annotations found for ${this.getSafeUserName(this.user1Id)} on this document.`
            });
            return; // Exit the method early
          } else if (!annotationData.user2.length) {
            // User 2 has no annotations
            this.$emit('no-annotations', {
              message: `No annotations found for ${this.getSafeUserName(this.user2Id)} on this document.`
            });
            return; // Exit the method early
          }
          
          // If we got here, both users have annotations
          this.user1Annotations = annotationData.user1;
          this.user2Annotations = annotationData.user2;
          this.apiLoaded = true;
          
          // If we're showing different users than requested, update debug info
          if (annotationData.user1.length > 0 
          && annotationData.user1[0].user !== parseInt(this.user1Id)) {
            this.errorMessage = `Showing annotations from users 1 and 38 instead of ${this.user1Id} and ${this.user2Id}`;
          }
        } catch (error) {
          console.error('Error fetching annotations:', error);
          this.$emit('no-annotations', {
            message: `Error loading annotations: ${error.message}`
          });
          return; // Exit the method early instead of using test data
        }
        
        // Calculate metrics
        this.calculateAgreementMetrics();
      } catch (error) {
        console.error('Error:', error);
        this.$emit('no-annotations', {
          message: `Couldnt connect to the database, try again later.`
        });
      } finally {
        this.loading = false;
      }
    },

    async fetchProjectLabels() {
      if (!this.labels || this.labels.length === 0) {
        try {
          // Try to fetch the labels from the project
          const labels = await this.$services.spanType.list(this.projectId);
          if (labels && labels.length > 0) {
            console.log("Fetched project labels:", labels.length);
            // Set the effective labels directly
            this.projectLabels = labels;
          } else {
            console.log("No project labels found, using defaults");
          }
        } catch (error) {
          console.error("Error fetching project labels:", error);
        }
      }
    },

    calculateAgreementMetrics() {
      // Reset counters
      this.matchingCount = 0;
      this.user1OnlyCount = 0;
      this.user2OnlyCount = 0;
      
      // Check for matching annotations
      for (const ann1 of this.user1Annotations) {
        const match = this.user2Annotations.find(
          ann2 => 
            ann1.start_offset === ann2.start_offset && 
            ann1.end_offset === ann2.end_offset && 
            ann1.label === ann2.label
        );
        
        if (match) {
          this.matchingCount++;
        } else {
          this.user1OnlyCount++;
        }
      }
      
      // Count annotations unique to user 2
      for (const ann2 of this.user2Annotations) {
        const match = this.user1Annotations.find(
          ann1 => 
            ann2.start_offset === ann1.start_offset && 
            ann2.end_offset === ann1.end_offset && 
            ann2.label === ann1.label
        );
        
        if (!match) {
          this.user2OnlyCount++;
        }
      }
    },

    // Add this new method for manual fetch
    async manualFetch() {
      this.errorMessage = null;
      try {
        // Use the annotation service
        const annotationData = await this.$services.annotation.getComparisonData(
          this.projectId,
          this.documentId,
          this.user1Id,
          this.user2Id
        );
        
        const user1Annot = annotationData.user1 || [];
        const user2Annot = annotationData.user2 || [];
        
        console.log("Manual fetch results:", { user1: user1Annot, user2: user2Annot });
        
        if (user1Annot.length > 0 || user2Annot.length > 0) {
          this.user1Annotations = user1Annot;
          this.user2Annotations = user2Annot;
          this.apiLoaded = true;
          this.calculateAgreementMetrics();
        } else {
          // If no annotations found, load test data
          this.useTestData();
        }
      } catch (error) {
        console.error("Manual fetch error:", error);
        this.errorMessage = error.message;
        // Load test data as fallback
        this.useTestData();
      }
    },
    
    // Fix the isMatchingAnnotation method
    isMatchingAnnotation(ann) {
      if (ann.user === 1) {
        return this.user2Annotations.some(a => 
          a.start_offset === ann.start &&
          a.end_offset === ann.end &&
          a.label === ann.label
        );
      } else {
        return this.user1Annotations.some(a => 
          a.start_offset === ann.start &&
          a.end_offset === ann.end &&
          a.label === ann.label
        );
      }
    },
    
    // Add this method to load test data (renamed from useTestData)
    loadTestData() {
      console.log("Loading test data");
      // Sample document text
      this.documentText = "This is a sample document text for demonstration purposes. It will help visualize annotations from different users."
      
      // Sample annotations
      this.user1Annotations = [
        { id: 101, start_offset: 5, end_offset: 11, label: 1 },
        { id: 102, start_offset: 27, end_offset: 38, label: 2 }
      ]
      
      this.user2Annotations = [
        { id: 201, start_offset: 5, end_offset: 11, label: 1 },
        { id: 202, start_offset: 44, end_offset: 54, label: 3 }
      ]
      
      // Calculate metrics
      this.calculateAgreementMetrics()
    },

    getSafeUserName(userId) {
      // First try to get from the users prop if available
      if (this.users && Array.isArray(this.users) && this.users.length > 0) {
        const user = this.users.find(u => u.id === parseInt(userId) || u.id === userId);
        if (user && user.username) {
          return user.username;
        }
      }

      // Otherwise just return User + ID
      return `User ${userId}`;
    },

    syncScroll(source, event) {
      // Prevent infinite scroll loop
      if (this.isScrollingSynced) return;
      
      this.isScrollingSynced = true;
      
      // Sync the other panel
      const sourceElement = event.target;
      const targetElement = source === 1 
        ? this.$refs.user2Content 
        : this.$refs.user1Content;
      
      targetElement.scrollTop = sourceElement.scrollTop;
      
      // Reset the flag after a short delay
      setTimeout(() => {
        this.isScrollingSynced = false;
      }, 50);
    }
  }
})
</script>

<style scoped>
.comparison-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #ffffff;
}

.header {
  border-bottom: 1px solid #e0e0e0;
}

.label-legend {
  border-bottom: 1px solid #e0e0e0;
}

.side-by-side-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  align-items: stretch; /* Make sure both sides stretch fully */
}

.document-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid #e0e0e0;
  width: 50%; /* Ensure equal width */
  min-width: 0; /* Allow flex container to shrink properly */
  box-sizing: border-box; /* Include padding in width calculation */
}

.document-panel:last-child {
  border-right: none;
}

.document-header {
  display: flex;
  align-items: center;
  background-color: #fafafa;
  border-bottom: 1px solid #e0e0e0;
}

.document-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden; /* Hide horizontal scrollbar */
  position: relative;
  height: 100%;
  padding: 16px; /* Ensure consistent padding */
}

.document-text {
  font-family: 'Roboto Mono', monospace;
  line-height: 1.7;
  white-space: pre-wrap; /* Allow text to wrap */
  font-size: 0.9rem;
  padding-bottom: 12px; /* Add padding for the scrollbar */
  word-break: break-word; /* Break long words if needed */
  width: 100%; /* Use full width */
  display: inline-block; /* Important for consistent rendering */
}

.agreement-stats-bar {
  background-color: #f5f5f5;
  border-top: 1px solid #e0e0e0;
}

.stats-container {
  max-width: 900px;
  margin: 0 auto;
}

.stats-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
  min-width: 150px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
}

.match-box {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.user1-box {
  background-color: #fff8e1;
  color: #f57f17;
}

.user2-box {
  background-color: #e3f2fd;
  color: #0d47a1;
}

.agreement-box {
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.user1-badge {
  background-color: #fff3e0;
  border: 2px solid #e65100;
}

.user2-badge {
  background-color: #e3f2fd;
  border: 2px solid #0d47a1;
}

.rounded {
  border-radius: 3px;
}

/* Style the highlight classes */
.highlight-match {
  background-color: #c8e6c9;
  border-radius: 2px;
}

.highlight-user1 {
  background-color: #ffecb3;
  border-radius: 2px;
}

.highlight-user2 {
  background-color: #bbdefb;
  border-radius: 2px;
}

/* Animation for matches */
.highlight-match {
  position: relative;
}

.highlight-match::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #4CAF50;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.6;
  }
}
</style>