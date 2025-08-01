// liquid-intelligence-system/media-processing/AudioRecorder.ts

/**
 * AudioRecorder - Real implementation for audio capture and processing
 * Replaces the simulated audio processing in the Liquid Intelligence system
 */

export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private stream: MediaStream | null = null;
  private isRecording: boolean = false;
  private startTime: number | null = null;
  
  /**
   * Start recording audio from user's microphone
   * @returns Promise that resolves when recording starts
   */
  async startRecording(): Promise<void> {
    if (this.isRecording) {
      console.warn('Audio recording is already in progress');
      return;
    }
    
    try {
      // Request audio permissions
      this.stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      this.audioChunks = [];
      this.isRecording = true;
      this.startTime = Date.now();
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };
      
      // Collect data every 1 second for real-time processing
      this.mediaRecorder.start(1000);
      
      console.log('Audio recording started');
    } catch (error) {
      console.error('Error starting audio recording:', error);
      this.isRecording = false;
      throw new Error(`Failed to start audio recording: ${error}`);
    }
  }
  
  /**
   * Stop recording and return the audio blob
   * @returns Promise that resolves with the recorded audio blob
   */
  stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.isRecording || !this.mediaRecorder) {
        return resolve(new Blob());
      }
      
      this.mediaRecorder.onstop = () => {
        try {
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm;codecs=opus' });
          
          // Stop all tracks to release microphone
          if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
          }
          
          this.isRecording = false;
          console.log(`Audio recording stopped. Recorded ${audioBlob.size} bytes`);
          resolve(audioBlob);
        } catch (error) {
          console.error('Error processing recorded audio:', error);
          reject(error);
        }
      };
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };
      
      this.mediaRecorder.stop();
    });
  }
  
  /**
   * Check if currently recording
   * @returns boolean indicating recording status
   */
  isCurrentlyRecording(): boolean {
    return this.isRecording;
  }
  
  /**
   * Get the current media stream
   * @returns MediaStream or null if not recording
   */
  getMediaStream(): MediaStream | null {
    return this.stream;
  }
  
  /**
   * Get recording duration in seconds
   * @returns number of seconds recorded
   */
  getRecordingDuration(): number {
    if (!this.mediaRecorder || !this.isRecording) {
      return 0;
    }
    
    // Calculate actual recording duration
    if (this.startTime) {
      return Math.floor((Date.now() - this.startTime) / 1000);
    } else {
      return 0;
    }
  }
}

export default AudioRecorder;
