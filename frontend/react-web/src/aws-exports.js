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
 * AWS Configuration
 * 
 * This module exports configuration settings for AWS services used by the application.
 * Values are populated during deployment from CloudFormation outputs.
 */

/**
 * AWS Amplify authentication configuration.
 * Contains Cognito User Pool and Identity Pool settings for user authentication.
 * 
 * @constant
 * @type {Object}
 * @property {string} Auth.Cognito.userPoolClientId - Cognito User Pool Client ID
 * @property {string} Auth.Cognito.userPoolId - Cognito User Pool ID
 * @property {string} Auth.Cognito.identityPoolId - Cognito Identity Pool ID
 * @property {string} Auth.Cognito.region - AWS region for Cognito services
 */
export const awsConfig = {
    Auth: {
        Cognito: {
            userPoolClientId: '3vp3u5oa581qejgcr63eijk3hh',
            userPoolId: 'us-east-1_J2ljpnicF',
            identityPoolId: 'us-east-1:448cf32d-8852-4bc6-a7e7-d8adbe7d2581',
            region: 'us-east-1'
        }
    }
}

/**
 * WebSocket API secret
 * 
 * @constant
 * @type {string}
 */
export const apiKey = "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" // Replace with your actual API key before running

/**
 * WebSocket endpoint URL
 * 
 * @constant
 * @type {string}
 */
export const apiUrl = "ws://Virtua-Virtu-9RjKo1Buhij1-b8b68f5b845e5563.elb.us-east-1.amazonaws.com/ws"

/**
 * Avatar .glb model filename
 * 
 * @constant
 * @type {string}
 */
export const avatarFileName = "sophia.glb"

/**
 * Avatar jaw bone name
 * 
 * @constant
 * @type {string}
 */
export const avatarJawboneName = "rp_sophia_animated_003_idling_jaw"
