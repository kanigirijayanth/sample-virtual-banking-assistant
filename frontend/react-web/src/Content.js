/*********************************************************************************************************************
*  Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                           *
*                                                                                                                    *
*  Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance        *
*  with the License. A copy of the License is located at                                                             *
*                                                                                                                    *
*      http://aws.amazon.com/asl/                                                                                    *
*                                                                                                                    *
*  or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES *
*  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions    *
*  and limitations under the License.                                                                                *
**********************************************************************************************************************/

/**
 * Main Content Component
 * 
 * This component handles the core functionality of the Virtual Banking Assistant,
 * including audio streaming, WebSocket communication, and avatar control.
 */

import React, { useState, useRef, useEffect } from 'react';
import { getCurrentUser, signOut } from 'aws-amplify/auth';
import { Authenticator } from '@aws-amplify/ui-react';
import { Navbar, Spinner, Modal, Button, Nav, NavDropdown } from 'react-bootstrap';

import Avatar from './Avatar'
import './App.css';
import { apiKey, apiUrl, avatarFileName, avatarJawboneName } from './aws-exports'

// Audio sample rate. It should match the same in the backend to avoid resampling overhead.
const SAMPLE_RATE = 16000;

/**
 * Content Component
 * Manages the authenticated user interface and audio communication
 * 
 * @param {Object} props Component properties
 * @param {Function} props.signOut Function to handle user sign out
 * @param {Object} props.user Current authenticated user
 */
function Content({ signOut, user }) {
    // State management
    const [messages, setMessages] = useState([]);
    const [isTalking, setTalking] = useState(false);
    const [headerVisible, setHeaderVisible] = useState(true);
    const [isEngaged, setEngaged] = useState(false);

    // Audio context and processing references
    const audioContextRef = useRef(null);
    const audioWorkletNodeRef = useRef(null);
    const wsRef = useRef(null);

    /**
     * Converts Float32Array audio data to 16-bit PCM format.
     * 
     * @param {Float32Array} input Audio data in float format
     * @returns {Int16Array} Audio data in 16-bit PCM format
     */
    const floatToPcm16 = (input) => {
        const output = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
            const s = Math.max(-1, Math.min(1, input[i]));
            output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return output;
    };

    /**
     * Converts 16-bit PCM audio data to Float32Array format.
     * 
     * @param {ArrayBuffer} buffer Audio data in PCM format
     * @returns {Float32Array} Audio data in float format
     */
    const pcm16ToFloat = (buffer) => {
        const dataView = new DataView(buffer);
        const float32 = new Float32Array(buffer.byteLength / 2);
        for (let i = 0; i < float32.length; i++) {
            const int16 = dataView.getInt16(i * 2, true);
            float32[i] = int16 / 32768.0;
        }
        return float32;
    };

    /**
     * Initializes audio context and AudioWorklet for audio processing
     */
    const initAudioWorklet = async () => {
        try {
            // Close any existing audio context
            if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
                await audioContextRef.current.close();
            }
            
            // Create new audio context
            audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: SAMPLE_RATE
            });
            
            console.log('Loading audio processor module...');
            await audioContextRef.current.audioWorklet.addModule('/audio-processor.js');
            console.log('Audio processor module loaded successfully');
            
            // Create AudioWorkletNode
            audioWorkletNodeRef.current = new AudioWorkletNode(
                audioContextRef.current,
                'audio-processor'
            );
            
            // Handle messages from audio processor
            audioWorkletNodeRef.current.port.onmessage = (event) => {
                if (event.data === 'needData') {
                    setTalking(false);
                }
            };
            
            // Connect to audio output
            audioWorkletNodeRef.current.connect(audioContextRef.current.destination);
            
            // Resume audio context
            if (audioContextRef.current.state !== 'running') {
                await audioContextRef.current.resume();
                console.log('Audio context resumed successfully');
            }
            
            console.log('AudioWorklet initialized successfully');
            return true;
        } catch (error) {
            console.error('Failed to initialize AudioWorklet:', error);
            return false;
        }
    };

    /**
     * Initializes microphone input for audio capture
     */
    const initMicrophone = async () => {
        try {
            // Request microphone access
            console.log('Requesting microphone access...');
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            console.log('Microphone access granted');
            
            // Create audio source from microphone stream
            const source = audioContextRef.current.createMediaStreamSource(stream);
            const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1);
            
            source.connect(processor);
            
            // Connect to destination with zero gain to prevent feedback
            const gainNode = audioContextRef.current.createGain();
            gainNode.gain.value = 0;
            processor.connect(gainNode);
            gainNode.connect(audioContextRef.current.destination);
            
            // Process and send audio data
            processor.onaudioprocess = (event) => {
                if (wsRef.current?.readyState !== WebSocket.OPEN) {
                    return; // Don't process audio if WebSocket is not open
                }
                
                try {
                    const input = event.inputBuffer.getChannelData(0);
                    const pcm16 = floatToPcm16(input);
                    const buffer = new ArrayBuffer(pcm16.length * 2);
                    const view = new DataView(buffer);
                    pcm16.forEach((value, index) => view.setInt16(index * 2, value, true));
                    const bytes = new Uint8Array(buffer);
                    const base64 = btoa(String.fromCharCode.apply(null, bytes));
                    
                    wsRef.current.send(base64);
                } catch (error) {
                    console.error('Error processing microphone data:', error);
                }
            };
            
            console.log('Microphone initialized successfully');
            return true;
        } catch (error) {
            console.error('Failed to initialize microphone:', error);
            
            // Show user-friendly error if microphone access is denied
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                alert('Microphone access is required for this application to work. Please allow microphone access and try again.');
            }
            
            return false;
        }
    };

    // Setup and cleanup effect
    useEffect(() => {
        let isComponentMounted = true;
        
        const cleanup = () => {
            console.log('Cleaning up audio and WebSocket resources');
            
            // Close WebSocket connection
            if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
                console.log('Closing WebSocket connection');
                wsRef.current.close(1000, 'User disengaged');
            }
            
            // Clean up audio context
            if (audioContextRef.current?.state !== 'closed') {
                console.log('Closing audio context');
                if (audioWorkletNodeRef.current) {
                    audioWorkletNodeRef.current.disconnect();
                }
                if (audioContextRef.current) {
                    audioContextRef.current.close().catch(err => {
                        console.error('Error closing audio context:', err);
                    });
                }
            }
        };

        if (!isEngaged) {
            cleanup();
            return;
        }

        // Initialize audio and WebSocket
        const initAudio = async () => {
            console.log('Initializing audio system...');
            const audioInitialized = await initAudioWorklet();
            
            if (!audioInitialized || !isComponentMounted) {
                console.log('Audio initialization failed or component unmounted');
                if (isComponentMounted) {
                    setEngaged(false);
                }
                return;
            }
            
            // Create WebSocket with timeout and retry logic
            const connectWebSocket = () => {
                try {
                    console.log('Attempting to connect WebSocket...');
                    wsRef.current = new WebSocket(apiUrl, apiKey);
                    
                    // Set a connection timeout
                    const connectionTimeout = setTimeout(() => {
                        if (wsRef.current && wsRef.current.readyState !== WebSocket.OPEN) {
                            console.log('WebSocket connection timeout, retrying...');
                            wsRef.current.close();
                            connectWebSocket();
                        }
                    }, 5000);
                    
                    wsRef.current.onopen = async () => {
                        console.log('WebSocket connected successfully');
                        clearTimeout(connectionTimeout);
                        await initMicrophone();
                    };
                    
                    wsRef.current.onmessage = async (event) => {
                        try {
                            const chunk = JSON.parse(event.data);
                            
                            if (chunk.event === 'stop') {
                                console.log('Interruption');
                                if (audioWorkletNodeRef.current) {
                                    audioWorkletNodeRef.current.port.postMessage({
                                        type: 'stop'
                                    });
                                }
                                setTalking(false);
                                
                            } else if (chunk.event === 'media') {
                                try {
                                    const base64Data = chunk.data;
                                    const binaryString = atob(base64Data);
                                    const bytes = new Uint8Array(binaryString.length);
                                    for (let i = 0; i < binaryString.length; i++) {
                                        bytes[i] = binaryString.charCodeAt(i);
                                    }
                                    
                                    const float32Array = pcm16ToFloat(bytes.buffer);
                                    
                                    if (float32Array.length > 0 && audioWorkletNodeRef.current) {
                                        audioWorkletNodeRef.current.port.postMessage({
                                            type: 'data',
                                            audio: float32Array
                                        });
                                        
                                        if (!isTalking) {
                                            setTalking(true);
                                        }
                                    }
                                } catch (error) {
                                    console.error('Error processing audio data:', error);
                                }
                            } else if (chunk.event === 'text') {
                                setMessages(messages => [...messages, {
                                    isMine: chunk.speaker === 'user',
                                    text: chunk.data
                                }]);
                            }
                        } catch (error) {
                            console.error('Error handling WebSocket message:', error);
                        }
                    };
                    
                    wsRef.current.onerror = (error) => {
                        console.error('WebSocket error:', error);
                        clearTimeout(connectionTimeout);
                        setTalking(false);
                    };
                    
                    wsRef.current.onclose = (event) => {
                        console.log(`WebSocket closed with code ${event.code}, reason: ${event.reason}`);
                        clearTimeout(connectionTimeout);
                        setTalking(false);
                        
                        // Only set engaged to false if we're intentionally closing
                        if (event.code !== 1000) {
                            console.log('Abnormal closure, not disengaging');
                        } else {
                            setEngaged(false);
                        }
                    };
                } catch (error) {
                    console.error('Error creating WebSocket:', error);
                }
            };
            
            // Initialize the WebSocket connection
            connectWebSocket();
        };

        initAudio();
        
        // Cleanup function for useEffect
        return () => {
            isComponentMounted = false;
            cleanup();
        };
    }, [isEngaged]);

    return (
        <div className="app">
            {/* Header with navigation */}
            <Navbar
                className='header'
                bg='light'
                expand='lg'
                style={{
                    transition: 'opacity 0.3s ease',
                    opacity: headerVisible ? 1 : 0,
                    pointerEvents: headerVisible ? 'auto' : 'none'
                }}
            >
                <Navbar.Brand className='px-2'>Virtual Cloud Operations Assistant</Navbar.Brand>
                {user &&
                    <Nav className='d-flex flex-row p-2 nav-strip flex-grow-1 justify-content-end'>
                        <Nav.Link onClick={() => setHeaderVisible(false)}>
                            Immersive
                        </Nav.Link>
                        <Nav.Link onClick={() => {
                            setEngaged(!isEngaged)
                            if (isEngaged) {
                                setTalking(false)
                            }
                        }}>
                            {isEngaged ? 'Disengage' : 'Engage'}
                        </Nav.Link>
                        <Nav.Link onClick={signOut}>
                            Logout
                        </Nav.Link>
                    </Nav>
                }
            </Navbar>

            {/* Main content area with avatar */}
            <div className="container" onClick={() => setHeaderVisible(true)}>
                <Avatar
                    glbUrl={"/" + avatarFileName}
                    jawBoneName={avatarJawboneName}
                    isTalking={isTalking}
                />
            </div>
        </div>
    );
}

export default Content;
