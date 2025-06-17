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

import { useState, useEffect } from 'react';
import {
    Button,
    Header,
    SpaceBetween,
    Spinner,
    Table,
    StatusIndicator
} from '@cloudscape-design/components';
import { API } from "aws-amplify";

export default function TableDetailsPanel({
    databaseConnectionState,
    setDatabaseConnectionState,
    databaseConnected,
    selectedSchemas,
    setGetTables
}) {

    const [tables, setTables] = useState([]);
    const [selectedItems, setSelectedItems] = useState([]);

    useEffect(() => {
        setDatabaseConnectionState((current) => {
            const body = { ...current.body, tables: selectedItems };
            return { ...current, body };
        });
    }, [selectedItems]);
    const [gettingSchema, setGettingSchema] = useState(false);
    const [gettingSchemaFailed, setGettingSchemaFailed] = useState(false);



    const getDatabaseSchema = async (e) => {
        setGettingSchema(true);
        const request = {
            ...databaseConnectionState,
            body: {
                ...databaseConnectionState.body,
                oracle_owner: selectedSchemas.map((s) => s.value).join(','),
            },
        };
        await API.post("api", "api/archive/source/get-schema", request)
            .then(response => {
                setGettingSchemaFailed(false)
                setTables(response.tables);
                setSelectedItems(response.tables);
                setPageCount(Math.ceil(response.tables.length / 10));
                setGettingSchema(false);
                updateNestedProps(response.tables)
                setGetTables(true)
            })
            .catch(error => {
                setGettingSchemaFailed(true)
                setGettingSchema(false);
            })
    };

    const updateNestedProps = (data) => {
        setDatabaseConnectionState(current => {
            const body = { ...current.body };
            body.tables = data;
            return { ...current, body };
        });
    };


    return (
        <Table
            columnDefinitions={[
                {
                    id: 'owner',
                    header: 'Owner',
                    cell: item => item.oracle_owner || item.mssql_schema || '',
                },
                {
                    id: 'table',
                    header: 'Table',
                    cell: item => item.table,
                },
                {
                    id: 'columns',
                    header: 'Columns',
                    cell: item => item.schema.length,
                },
            ]}
            items={tables}
            selectedItems={selectedItems}
            selectionType="multi"
            onSelectionChange={({ detail }) => setSelectedItems(detail.selectedItems)}
            header={
                <Header
                    counter={
                        selectedItems.length
                            ? `(${selectedItems.length}/${tables.length})`
                            : `(${tables.length})`
                    }
                    actions={
                        <SpaceBetween direction="horizontal" size="xs">
                            {gettingSchema ? (
                                <Button variant="primary">
                                    <Spinner />
                                </Button>
                            ) : (
                                <Button
                                    disabled={!databaseConnected}
                                    onClick={getDatabaseSchema}
                                    variant="primary"
                                >
                                    Fetch Tables
                                </Button>
                            )}
                            {gettingSchemaFailed && (
                                <StatusIndicator type="error">
                                    Failed to Fetch Tables
                                </StatusIndicator>
                            )}
                        </SpaceBetween>
                    }
                >
                    Table Details
                </Header>
            }
            pagination={null}
        />
    );
}