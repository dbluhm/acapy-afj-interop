import {
  InitConfig,
  Agent,
  KeyDerivationMethod,
  ConsoleLogger,
  LogLevel,
  KeyDidCreateOptions,
  KeyType,
  DidKey,
  JwaSignatureAlgorithm,
  ConnectionEventTypes,
  HttpOutboundTransport,
} from '@aries-framework/core';
import { agentDependencies } from '@aries-framework/node';
import { AskarModule } from '@aries-framework/askar';
import { ariesAskar } from '@hyperledger/aries-askar-nodejs';
import { TCPSocketServer, JsonRpcApiProxy } from 'json-rpc-api-proxy';

let agent: Agent | null;
const server = new TCPSocketServer({
  host: process.env.AFJ_HOST || '0.0.0.0',
  port: parseInt(process.env.AFJ_PORT || '3000'),
});
const proxy = new JsonRpcApiProxy(server);

proxy.rpc.addMethod('initialize', async (): Promise<{}> => {
  const key = ariesAskar.storeGenerateRawKey({});

  const config: InitConfig = {
    label: 'test-agent',
    logger: new ConsoleLogger(LogLevel.debug),
    walletConfig: {
      id: 'test',
      key: key,
      keyDerivationMethod: KeyDerivationMethod.Raw,
      storage: {
        type: 'sqlite',
        inMemory: true,
      },
    },
  };

  agent = new Agent({
    config,
    dependencies: agentDependencies,
    modules: {
      // Register the Askar module on the agent
      askar: new AskarModule({
        ariesAskar,
      }),
    },
  });

  agent.registerOutboundTransport(new HttpOutboundTransport());

  const eventPassThrough = (type: string) => {
    agent?.events.on(type, async (event) => {
        proxy.rpc.notify("event." + type, event)
      }
    )
  };

  eventPassThrough(ConnectionEventTypes.ConnectionStateChanged)

  await agent.initialize();
  return {};
});


const getAgent = () => {
  if (agent === null) {
    throw new Error('Agent not initialized');
  }
  return agent;
};


proxy.rpc.addMethod('receiveInvitation', async ({invitation}: {invitation: string}) => {
  const agent = getAgent();
  const {outOfBandRecord} = await agent.oob.receiveInvitationFromUrl(invitation);
  return outOfBandRecord;
});

proxy.start();
