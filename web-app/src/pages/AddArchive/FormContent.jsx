/**
 * Copyright 2023 Amazon.com, Inc. and its affiliates. All Rights Reserved.
 *
 * Licensed under the Amazon Software License (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *   http://aws.amazon.com/asl/
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */

import { useState } from 'react';
import { useHistory } from "react-router-dom";
import {
    Button,
    Form,
    SpaceBetween,
    Spinner,
    Tabs,
} from '@cloudscape-design/components';
import TableDetailsPanel from './TableDetailsPanel';
import DatabaseTypePanel from './DatabaseTypePanel';
import DatabaseSettingsPanel from './DatabaseSettingsPanel';
import S3TargetPanel from './S3TargetPanel';
import { API } from "aws-amplify";



function BaseFormContent({ databaseConnectionState, targetState, databaseConnected, content, onCancelClick, getTables, errorText = null }) {

    const history = useHistory();
    const [creatingArchive, setCreatingArchive] = useState(false);

    const createArchive = async (e) => {
        setCreatingArchive(true);
        const request = {
            ...databaseConnectionState,
            body: {
                ...databaseConnectionState.body,
                ...targetState.body,
            },
        };
        await API.post("api", "api/archive/create", request);
        setCreatingArchive(false);
        history.push("/");
    };

    return (
        <form onSubmit={event => event.preventDefault()}>
            <Form
                actions={
                    <SpaceBetween direction="horizontal" size="xs">
                        <Button
                            disabled={creatingArchive}
                            variant="link" onClick={onCancelClick}>
                            Cancel
                        </Button>

                        {creatingArchive ? (
                            <Button variant="primary">
                                <Spinner />
                            </Button>
                        ) : (
                            <Button
                                disabled={!databaseConnected || creatingArchive || !getTables}
                                onClick={createArchive}
                                variant="primary"
                            >
                                Create archive
                            </Button>
                        )}

                    </SpaceBetween>
                }
                errorText={errorText}
                errorIconAriaLabel="Error"
            >
                {content}
            </Form>
        </form>
    );
}

export function FormContent({
    setFlashbarItems,
    setEnableFlashbar
}) {

    const [databaseConnectionState, setDatabaseConnectionState] = useState({ body: {} });
    const [targetState, setTargetState] = useState({ body: {} });
    const [databaseEngine, setDatabaseEngine] = useState();
    const [activeTab, setActiveTab] = useState('source');
    const [databaseConnected, setDatabaseConnected] = useState(false);
    const [getTables, setGetTables] = useState(false);
    const [schemaOptions, setSchemaOptions] = useState([]);
    const [selectedSchemas, setSelectedSchemas] = useState([]);

    return (
        <BaseFormContent
            databaseConnectionState={databaseConnectionState}
            targetState={targetState}
            setDatabaseConnectionState={setDatabaseConnectionState}
            databaseConnected={databaseConnected}
            setDatabaseConnected={setDatabaseConnected}
            getTables={getTables}
            content={
                <Tabs
                    onChange={({ detail }) => setActiveTab(detail.activeTabId)}
                    activeTabId={activeTab}
                    tabs={[
                        {
                            label: 'Source',
                            id: 'source',
                            content: (
                                <SpaceBetween size="l">
                                    <DatabaseTypePanel setDatabaseEngine={setDatabaseEngine} databaseEngine={databaseEngine} />
                                    <DatabaseSettingsPanel
                                        setDatabaseEngine={setDatabaseEngine}
                                        databaseEngine={databaseEngine}
                                        databaseConnectionState={databaseConnectionState}
                                        setDatabaseConnectionState={setDatabaseConnectionState}
                                        databaseConnected={databaseConnected}
                                        setDatabaseConnected={setDatabaseConnected}
                                        setFlashbarItems={setFlashbarItems}
                                        setEnableFlashbar={setEnableFlashbar}
                                        schemaOptions={schemaOptions}
                                        setSchemaOptions={setSchemaOptions}
                                        selectedSchemas={selectedSchemas}
                                        setSelectedSchemas={setSelectedSchemas}
                                    />
                                </SpaceBetween>
                            ),
                        },
                        {
                            label: 'Tables',
                            id: 'tables',
                            content: (
                                <TableDetailsPanel
                                    databaseConnectionState={databaseConnectionState}
                                    setDatabaseConnectionState={setDatabaseConnectionState}
                                    databaseConnected={databaseConnected}
                                    setDatabaseConnected={setDatabaseConnected}
                                    setGetTables={setGetTables}
                                    selectedSchemas={selectedSchemas}
                                />
                            ),
                        },
                        {
                            label: 'Target',
                            id: 'target',
                            content: (
                                <S3TargetPanel targetState={targetState} setTargetState={setTargetState} />
                            ),
                        },
                    ]}
                />
            }
        />
    );
}
